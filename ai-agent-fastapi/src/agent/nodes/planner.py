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
        return {}

    # Find the latest Human message
    latest_human_msg = next((msg for msg in reversed(messages) if isinstance(msg, HumanMessage)), None)
    if not latest_human_msg:
        # If no human message (e.g. tool result), skip planning.
        return {}
        
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
    
    CRITICAL RULE FOR LOCATIONS:
    If you plan to add a stop to an itinerary, your checklist MUST include calling `find_and_register_place` first to obtain the Google Place ID. You cannot use `add_stop` without a valid Place ID. DO NOT fetch Place IDs just to talk about them; only fetch them if you are about to add a stop.
    
    Do NOT execute the actions. Just write the checklist.
    Example: ["Fetch user dietary restrictions", "Search web for trendy Sushi restaurants", "Register top sushi restaurant with find_and_register_place", "Add registered sushi restaurant to itinerary"]
    """
    
    try:
        logger.info("Planner Node: Generating CoT checklist...")
        # We invoke the LLM with the system prompt and the latest user message
        result = structured_llm.invoke([
            SystemMessage(content=system_prompt),
            latest_human_msg
        ])
        
        # Reset retry_count on new plan
        return {
            "plan": result.steps,
            "retry_count": 0,
            "critic_feedback": ""
        }
    except Exception as e:
        logger.error(f"Planner Node failed: {e}")
        return {"plan": ["Acknowledge user request.", "Proceed with default execution."]}
