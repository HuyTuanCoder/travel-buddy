from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import logging
import os

from src.schemas.agent import AgentState

logger = logging.getLogger(__name__)

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
        
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro-latest",
        temperature=0, # Strict reasoning requires 0 temp
        api_key=os.getenv("GEMINI_API_KEY")
    )
    
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
    
    Do NOT execute the actions. Just write the checklist.
    Example: ["Fetch user dietary restrictions", "Search for Sushi restaurants", "Add top sushi restaurant to itinerary"]
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
