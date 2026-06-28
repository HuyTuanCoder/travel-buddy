from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
import structlog
import asyncio
import os
import json

from src.schemas.agent import AgentState
from src.core.config import get_llm
from src.core.telemetry import publish_thought
from langchain_core.runnables import RunnableConfig
from src.core.error_handlers import node_error_boundary

logger = structlog.get_logger(__name__)

class PlanChecklist(BaseModel):
    steps: list[str] = Field(
        description="A strict, step-by-step checklist of actions to fulfill the user's request."
    )

@node_error_boundary
async def plan_itinerary(state: AgentState, config: RunnableConfig):
    """
    Gate 1: The Planner Node.
    Forces the AI to generate a strict reasoning trace before executing tools.
    """
    thread_id = config.get("configurable", {}).get("thread_id", "")
    if thread_id:
        await publish_thought(f"stream:{thread_id}", "Analyzing request constraints and building step-by-step checklist...")

    messages = state.get("messages", [])
    if not messages:
        return {"plan": []}

    from src.agent.utils import get_conversational_transcript
    transcript = get_conversational_transcript(messages, turns=6)
    # Find the latest Human message to emphasize the immediate request
    latest_human_msg = next((msg for msg in reversed(messages) if isinstance(msg, HumanMessage)), None)
    latest_request = latest_human_msg.content if latest_human_msg else "Continue execution."
        
    llm = get_llm(temperature=0)
    
    structured_llm = llm.with_structured_output(PlanChecklist)
    
    # Extract the RAG context and the current draft from the state
    rag_context = state.get("rag_context", "")
    itinerary_draft = state.get("itinerary_draft", {})
    user_modifications = state.get("user_modifications", {})
    draft_context = json.dumps(itinerary_draft, indent=2) if itinerary_draft else "The draft is currently empty."
    user_mod_context = json.dumps(user_modifications, indent=2) if user_modifications else "No manual user modifications detected."
            
    system_prompt = f"""
    You are the Master Itinerary Planner. 
    Your job is to read the user's request, the known constraints, and the CURRENT ITINERARY DRAFT, and generate a strict, linear checklist of actions for an executor agent to follow.
    
    IMPORTANT STATE RULES:
    1. If you see an item in the draft with `"is_draft_deleted": true`, it means it was softly removed (ghosted). Do NOT recreate it from scratch if the user asks for it back. Use the RESTORE tools.
    
    Known Constraints & Memories:
    {rag_context}
    
    PREVIOUS EVENTS (Summary of dropped messages):
    {state.get("running_summary", "")}
    
    CURRENT ITINERARY DRAFT:
    {draft_context}
    
    USER MODIFICATIONS METADATA (Hierarchy of Truth - Level 2):
    {user_mod_context}
    
    CRITICAL INSTRUCTIONS:
    1. Hierarchy of Truth: 
       - LEVEL 1 (Highest): The User's Latest Request below. If they ask to override a rule or a manual edit, you MUST obey.
       - LEVEL 2: The USER MODIFICATIONS METADATA. If a stop has `isUserModified: true` in this JSON, it means the user explicitly dragged/edited it in their UI sandbox. Treat it as UNTOUCHABLE ground truth. DO NOT move or delete it unless Level 1 explicitly asked you to!
       - LEVEL 3 (Lowest): Previous known constraints (RAG Context).
       
    2. EXPERT TRAVEL AGENT CONSULTATION PHASES (STATE-AWARE PLANNING):
       You MUST evaluate the entire conversation history to determine which Phase we are currently in. You MUST ONLY output a plan for the CURRENT TURN. Do NOT output a multi-phase plan. Once your plan for the turn is complete, the graph will pause and wait for the user.

       - PHASE 1: Consultation & Discovery (The "Why" & "What")
         Condition: The user has provided a destination but lacks basic constraints (dates, budget) OR hasn't shared the "vibe" or emotional goal of the trip.
         Action: Output a plan to ask open-ended, discovery-based questions (e.g., "What do you want this vacation to feel like?"). YOU ARE BANNED FROM DRAFTING OR PITCHING.

       - PHASE 2: Collaborative Gathering Loop (The "Where" & "When")
         Condition: Basic constraints are known, but you do NOT yet have a comprehensive list of CONFIRMED points of interest (POIs), timing preferences, and pacing details for the entire trip.
         Action: Output a plan to use `search_web` (encourage using it IN PARALLEL for different categories like restaurants vs activities if applicable) to find POIs that match the vibe, present curated options, and actively ask logistical questions.
         Rule: You MUST stay in this phase across multiple turns to build a massive repository of confirmed preferences in the chat history.
         CRITICAL UX RULE: When instructing the agent to present multiple options, you MUST explicitly command it to be CONCISE (e.g. "Present 3 options concisely using bullet points and 1-sentence highlights"). Do NOT instruct it to write massive paragraphs. YOU ARE BANNED FROM DRAFTING. For long trips (4+ days), you do NOT need to gather context for the entire trip before drafting. Once you have a few solid ideas, you may end your plan by instructing the agent to ask: "Are you ready for me to put these ideas onto the board for the first couple of days so we can visualize it?"

       - PHASE 3: Itinerary Design (The Draft)
         Condition: The user has explicitly consented to drafting (e.g., "Yes, make the draft now") AFTER the Phase 2 gathering loop is complete.
         Action: Output a plan to officially lock in the confirmed POIs using `find_and_register_place` (encourage IN PARALLEL if multiple places), create the skeleton using `draft_add_day`, and schedule everything using `draft_add_stop` (encourage IN PARALLEL if scheduling multiple stops) according to their preferred pacing and timing. It is perfectly fine if the initial draft is incomplete or only covers the first few days (especially for long trips). The goal is to quickly get a visual skeleton on the board so the user can use the UI tools (add, move, swap) to fill in the blanks interactively.

       - PHASE 4: Refinement (Post-Draft)
         Condition: A draft exists, and the user is asking for tweaks.
         Action: Output a plan to use `draft_update_stop`, `draft_move_stop`, or `draft_remove_stop` to polish the itinerary.

    3. DEEP RESEARCH CHAINING: Actively encourage the agent to use `search_web` to discover URLs in Phase 2. IF AND ONLY IF the search snippets are not detailed enough, explicitly command the agent to use `read_webpage` on the specific URL returned by the search.
    
    4. LONG-TERM MEMORY (AGENTIC RAG): If the user refers to past conversations, past preferences, or says things like 'remember what I told you', you MUST instruct the agent to use the `search_past_conversations` tool.
    
    5. PARALLEL TOOL EXECUTION & RECURSION LIMITS (CRITICAL): The execution graph has a strict recursion limit of 25 loops. If you output 20 separate checklist items, the system will crash before it finishes. You MUST group parallel actions into a SINGLE checklist item. NEVER output more than 4-5 steps total in your array. If you are registering 9 places, combine them into ONE step: "Register Alum Cave, Newfound Gap, and 7 other places IN PARALLEL using `find_and_register_place`". If you are adding 5 stops to a day, combine them into ONE step: "Add the 5 stops to Day 1 IN PARALLEL using `draft_add_stop`".
    
    Do NOT execute the actions. Just write the checklist. Your array MUST NOT exceed 5 items.
    Example Phase 1: ["Push back and ask user for trip duration, budget, and the vibe they are looking for"]
    Example Phase 2: ["Search web for trendy Sushi restaurants", "Present top 2 sushi options to the user and ask if they prefer an early or late dinner reservation"]
    Example Phase 3: ["Register the 3 confirmed POIs (The Louvre, Eiffel Tower, and the sushi restaurant) IN PARALLEL with find_and_register_place", "Append them to Day 1 IN PARALLEL using draft_add_stop ensuring chronological order (Morning -> Afternoon -> Evening)"]
    """
    
    logger.info("Planner Node: Generating CoT checklist...")
    
    # Combine system prompt, recent transcript, and immediate request into a single string to avoid Gemini SystemMessage ordering bugs
    combined_prompt = f"{system_prompt}\n\nRECENT CHAT HISTORY:\n{transcript}\n\nIMMEDIATE USER REQUEST:\n{latest_request}"

    
    # We invoke the LLM with the combined prompt
    plan_output = structured_llm.invoke(combined_prompt)
    
    if hasattr(plan_output, 'steps'):
        steps = plan_output.steps
    elif isinstance(plan_output, list) and len(plan_output) > 0 and isinstance(plan_output[0], dict):
        # Handle langchain-google-vertexai 1.0.4 returning raw OpenAI tool schema format
        steps = plan_output[0].get("args", {}).get("steps", [])
    else:
        steps = []
        
    if thread_id and steps:
        formatted_steps = "\n> ".join(steps)
        await publish_thought(f"stream:{thread_id}", f"\n\n> Created Execution Plan:\n> {formatted_steps}\n")
    
    # Reset retry_count on new plan
    return {
        "plan": steps,
        "retry_count": 0,
        "critic_feedback": ""
    }