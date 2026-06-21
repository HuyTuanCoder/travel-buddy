from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, RemoveMessage, ToolMessage, AIMessage
import logging
import os

from src.schemas.agent import AgentState

logger = logging.getLogger(__name__)

class CriticEvaluation(BaseModel):
    is_valid: bool = Field(
        description="True if the itinerary is flawless and adheres to all constraints. False if there are logical errors or rule violations."
    )
    feedback: str = Field(
        description="If invalid, provide strict, scathing feedback on exactly what went wrong and how to fix it. If valid, leave empty."
    )

def evaluate_itinerary(state: AgentState):
    """
    Gate 3: The Critic Node (Reflexion).
    Evaluates the agent's work. If it fails, it violently loops back to the agent.
    Also implements the Intra-Turn State Collapser to prevent OOM errors.
    """
    messages = state.get("messages", [])
    retry_count = state.get("retry_count", 0)
    
    # 1. FAILSAFE: If we hit 3 retries, force a pass to avoid infinite loop
    if retry_count >= 3:
        logger.warning("CRITIC FAILSAFE: Max retries (3) hit. Forcing approval to prevent infinite loop.")
        return {
            "critic_feedback": "",
            # We don't increment retry_count here, just let it pass
        }
        
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro-latest",
        temperature=0, 
        api_key=os.getenv("GEMINI_API_KEY")
    )
    
    structured_llm = llm.with_structured_output(CriticEvaluation)
    
    # Reconstruct the full conversation context for the Critic
    context_str = "\n".join([f"{msg.type}: {msg.content}" for msg in messages if msg.content])
    
    system_prompt = f"""
    You are a ruthless, world-class Travel Critic.
    Review the proposed conversation and itinerary updates below.
    
    Check for:
    1. Geographic impossibilities (e.g., driving from NY to London).
    2. Scheduling impossibilities (e.g., visiting a museum at 3:00 AM).
    3. Constraint violations (e.g., recommending a steakhouse if the RAG SystemMessage says the user is Vegan).
    
    Conversation Log:
    {context_str}
    
    If it is flawless, set is_valid to true.
    If it has errors, set is_valid to false and provide scathing, explicit instructions on how the agent must fix it.
    """
    
    try:
        logger.info(f"Critic Node: Evaluating itinerary (Retry {retry_count}/3)...")
        evaluation = structured_llm.invoke(system_prompt)
        
        if evaluation.is_valid:
            logger.info("Critic Node: APPROVED.")
            return {"critic_feedback": ""}
        else:
            logger.warning(f"Critic Node: REJECTED. Feedback: {evaluation.feedback}")
            
            # --- THE INTRA-TURN STATE COLLAPSER ---
            # If the critic rejects, we do NOT want to append this entire failure trace 
            # to the LangGraph state. It will bloat the context window.
            # We will generate RemoveMessage commands for the recent failed AI & Tool messages.
            
            # Find the last Human Message index
            last_human_idx = -1
            for i in range(len(messages) - 1, -1, -1):
                if messages[i].type == "human":
                    last_human_idx = i
                    break
                    
            drop_commands = []
            if last_human_idx != -1:
                # We drop everything AFTER the last human message
                for msg in messages[last_human_idx + 1:]:
                    if msg.id:
                        drop_commands.append(RemoveMessage(id=msg.id))
            
            return {
                "critic_feedback": f"CRITIC REJECTION: {evaluation.feedback}",
                "retry_count": retry_count + 1,
                "messages": drop_commands # This physically deletes the bad history!
            }
            
    except Exception as e:
        logger.error(f"Critic Node failed: {e}")
        # If the critic crashes, default to pass
        return {"critic_feedback": ""}
