from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
import structlog
import os

from src.schemas.agent import AgentState
from src.core.config import get_llm

logger = structlog.get_logger(__name__)

class PlanChecklist(BaseModel):
    steps: list[str] = Field(
        description="A strict, step-by-step checklist of actions to fulfill the user's request."
    )

def plan_itinerary(state: AgentState):
    """
    Gate 1: The Planner Node.
    Forces the AI to generate a strict reasoning trace before executing tools.
    """
    messages = state.get("messages", [])
    if not messages:
        return {"plan": []}

    # Find the latest Human message
    latest_human_msg = next((msg for msg in reversed(messages) if isinstance(msg, HumanMessage)), None)
    if not latest_human_msg:
        # If no human message (e.g. tool result), skip planning.
        return {"plan": []}
        
    llm = get_llm(temperature=0)
    
    structured_llm = llm.with_structured_output(PlanChecklist)
    
    # Extract the RAG context (SystemMessage) if it exists
    rag_context = ""
    for msg in messages:
        if isinstance(msg, SystemMessage):
            rag_context += msg.content + "\n"
            
    system_prompt = f"""
    You are the Master Itinerary Planner. 
    Your job is to read the user's request and the known constraints, and generate a strict, linear checklist of actions for an executor agent to follow.
    
    Known Constraints & Memories:
    {rag_context}
    
    CRITICAL PLANNING RULES:
    1. VAGUE REQUESTS: If the user simply says "Plan a trip to X" with no dates, budget, or preferences, DO NOT generate a plan to build the itinerary. Instead, output a plan to: "Ask the user clarifying questions about dates, budget, and dietary preferences."
    2. THE DRAFT STATE: The Agent maintains an in-memory `itinerary_draft`. You must instruct the agent to build the trip incrementally into this draft. Do NOT instruct the agent to call database tools (`add_stop`) until the user explicitly says "Build this" or "I approve the draft".
    3. REAL-TIME DISCOVERY: Do not just rely on places you memorized in your training data. You should actively encourage the agent to use `search_web` to discover "what is currently popular", "hidden gems", or "highly rated new restaurants" to build a truly modern and exciting itinerary.
    4. LOCATIONS: If you plan to add a stop to the draft, your checklist MUST include calling `find_and_register_place` first to obtain the Google Place ID.
    
    Do NOT execute the actions. Just write the checklist.
    Example Vague: ["Push back and ask user for trip duration, budget, and preferences"]
    Example Detailed: ["Search web for trendy Sushi restaurants", "Register top sushi restaurant with find_and_register_place", "Append registered sushi restaurant to the itinerary_draft", "Show draft to user for approval"]
    """
    
    try:
        logger.info("Planner Node: Generating CoT checklist...")
        
        # Combine system prompt and user message into a single string to avoid Gemini SystemMessage ordering bugs with structured output
        combined_prompt = f"{system_prompt}\n\nUSER REQUEST:\n{latest_human_msg.content}"
        
        # We invoke the LLM with the combined prompt
        plan_output = structured_llm.invoke(combined_prompt)
        
        # Fallback: Sometimes Gemini returns a raw list instead of the Pydantic object
        steps = plan_output.steps if hasattr(plan_output, 'steps') else plan_output if isinstance(plan_output, list) else []
        
        # Reset retry_count on new plan
        return {
            "plan": steps,
            "retry_count": 0,
            "critic_feedback": ""
        }
    except Exception as e:
        logger.error(f"Planner Node failed: {e}")
        return {"plan": ["Acknowledge user request.", "Proceed with default execution."]}
