from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
import structlog
import asyncio
import os

from src.schemas.agent import AgentState
from src.core.config import get_llm
from src.core.telemetry import publish_thought
from langchain_core.runnables import RunnableConfig

logger = structlog.get_logger(__name__)

class PlanChecklist(BaseModel):
    steps: list[str] = Field(
        description="A strict, step-by-step checklist of actions to fulfill the user's request."
    )

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
    import json
    draft_context = json.dumps(itinerary_draft, indent=2) if itinerary_draft else "The draft is currently empty."
    user_mod_context = json.dumps(user_modifications, indent=2) if user_modifications else "No manual user modifications detected."
            
    system_prompt = f"""
    You are the Master Itinerary Planner. 
    Your job is to read the user's request, the known constraints, and the CURRENT ITINERARY DRAFT, and generate a strict, linear checklist of actions for an executor agent to follow.
    
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
       
       2. Dynamic Incremental Drafting:
       - Assess how much detail the user provided in their Latest Request.
       - If they ask for a massive multi-day trip but provide almost NO specifics (e.g. "Plan a 14 day trip"), use `draft_add_day` in parallel to create the skeleton (Days 1-14), but ONLY populate Day 1 with `draft_add_stop`. Stop there and ask for feedback!
       - HOWEVER, if they explicitly outline their ideas for multiple days (e.g. "Day 1 Beach, Day 2 Museum"), boldly generate all those days in full to match their detail. Use your judgement.
    
    CRITICAL PLANNING RULES:
    1. VAGUE REQUESTS: If the user simply says "Plan a trip to X" with no dates, budget, or preferences, DO NOT generate a plan to build the itinerary. Instead, output a plan to: "Ask the user clarifying questions about dates, budget, and dietary preferences."
    
    2. EXECUTION WAVES (CRITICAL DEPENDENCY CHAIN): 
       You MUST structure your plan in sequential waves, while encouraging parallel execution INSIDE each wave. The Agent CANNOT call `draft_add_stop` if it doesn't have a `google_place_id` yet!
       - WAVE 1 (Structure & Discovery): Instruct the Agent to call `draft_add_day` (multiple times in parallel if needed) AND `search_web` in parallel. Then WAIT for results.
       - WAVE 2 (Registration): Instruct the Agent to call `find_and_register_place` multiple times in parallel for the discovered places. Then WAIT for the IDs.
       - WAVE 3 (Drafting): Instruct the Agent to call `draft_add_stop` multiple times in parallel using the registered IDs.
       
    3. DEEP RESEARCH CHAINING: Actively encourage the agent to use `search_web` to discover URLs. IF AND ONLY IF the search snippets are not detailed enough, explicitly command the agent to use `read_webpage` on the specific URL returned by the search. Do NOT assume the agent will do this on its own.
    
    1-SHOT EXAMPLE OF A PERFECT PLAN:
    User Request: "Let's plan day 1 in Paris. I want to visit the Louvre, get some sushi, and then see the Eiffel Tower."
    Output:
    [
      "WAVE 1: Check RAG constraints for sushi preferences. Call search_web to find the best sushi near the Louvre.",
      "WAVE 2: Call find_and_register_place 3 times in parallel for 'The Louvre Paris', 'The Sushi Restaurant you found', and 'Eiffel Tower Paris'.",
      "WAVE 3: Call draft_add_stop 3 times in parallel to add the registered locations to Day 1, ensuring the times are sequential (Morning -> Lunch -> Afternoon)."
    ]
    5. LONG-TERM MEMORY (AGENTIC RAG): If the user refers to past conversations, past preferences, or says things like 'remember what I told you', you MUST instruct the agent to use the `search_past_conversations` tool. If this tool returns no results, DO NOT guess or hallucinate. Instruct the agent to apologize to the user and ask them to remind you what they said.
    
    Do NOT execute the actions. Just write the checklist.
    Example Vague: ["Push back and ask user for trip duration, budget, and preferences"]
    Example Detailed: ["Search web for trendy Sushi restaurants", "Register top sushi restaurant with find_and_register_place", "Append registered sushi restaurant to the itinerary_draft", "Show draft to user for approval"]
    """
    
    try:
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
    except Exception as e:
        logger.error(f"Planner Node failed: {e}")
        return {"plan": ["Acknowledge user request.", "Proceed with default execution."]}
