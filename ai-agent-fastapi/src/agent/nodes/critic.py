from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, RemoveMessage, ToolMessage, AIMessage
import structlog
import asyncio
import os

from src.schemas.agent import AgentState
from src.core.config import get_llm
from src.core.telemetry import publish_thought
from langchain_core.runnables import RunnableConfig

logger = structlog.get_logger(__name__)

class CriticEvaluation(BaseModel):
    is_valid: bool = Field(
        description="True if the itinerary is flawless and adheres to all constraints. False if there are logical errors or rule violations."
    )
    feedback: str = Field(
        description="If invalid, provide strict, scathing feedback on exactly what went wrong and how to fix it. If valid, leave empty."
    )

async def evaluate_itinerary(state: AgentState, config: RunnableConfig):
    """
    Gate 3: The Critic Node (Reflexion).
    Evaluates the agent's work. If it fails, it violently loops back to the agent.
    Also implements the Intra-Turn State Collapser to prevent OOM errors.
    """
    thread_id = config.get("configurable", {}).get("thread_id", "")
    if thread_id:
        await publish_thought(f"stream:{thread_id}", "Critic evaluating proposed itinerary against constraints...")

    messages = state.get("messages", [])
    retry_count = state.get("retry_count", 0)
    itinerary_draft = state.get("itinerary_draft", {})
    
    # 1. FAILSAFE: If we hit 3 retries, force a pass to avoid infinite loop
    if retry_count >= 3:
        logger.warning("CRITIC FAILSAFE: Max retries (3) hit. Forcing approval to prevent infinite loop.")
        return {
            "critic_feedback": "",
            # We don't increment retry_count here, just let it pass
        }
        
    llm = get_llm(temperature=0)
    
    structured_llm = llm.with_structured_output(CriticEvaluation)
    
    # Reconstruct the full conversation context for the Critic
    from src.agent.utils import get_conversational_transcript
    context_str = get_conversational_transcript(messages, turns=5)
    
    import json
    draft_str = json.dumps(itinerary_draft, indent=2) if itinerary_draft else "{}"
    
    rag_context = state.get("rag_context", "")
    rag_injection = f"\n{rag_context}\n" if rag_context else ""
    
    system_prompt = f"""
    You are a ruthless, world-class Travel Critic.
    Review the Agent's proposed actions and the current ITINERARY DRAFT below.
    {rag_injection}
    Check for:
    1. Geographic impossibilities (e.g., driving from NY to London).
    2. Scheduling impossibilities (e.g., visiting a museum at 3:00 AM).
    3. SEMANTIC VIOLATIONS: Does the draft actually align with what the user requested in the conversation log? If they asked for cheap vegan food, and the draft contains an expensive steakhouse, REJECT IT.
    
    Current Itinerary Draft:
    {draft_str}
    
    Recent Conversation Log:
    {context_str}
    
    If it is flawless, set is_valid to true.
    If it has errors or semantic violations, set is_valid to false and provide scathing, explicit instructions on how the agent must fix it.
    
    1-SHOT EXAMPLE OF PERFECT CRITIQUE:
    Draft: User is going to Tokyo. Added a stop to visit a museum at 3:00 AM.
    Constraint Log: User wants a cheap trip.
    Output:
    {{
      "is_valid": false,
      "feedback": "CRITICAL ERROR: You scheduled a museum visit at 3:00 AM! Museums are closed. Furthermore, you failed to check if the museum is cheap. Delete this stop immediately, call search_web to find cheap museums open during the day, and draft a new stop."
    }}
    """
    
    try:
        logger.info(f"Critic Node: Evaluating draft (Retry {retry_count}/3)...")
        evaluation = structured_llm.invoke(system_prompt)
        
        # Fallback for Gemini returning a raw dict instead of Pydantic model
        if isinstance(evaluation, dict):
            is_valid = evaluation.get("is_valid", True)
            feedback = evaluation.get("feedback", "")
        else:
            is_valid = getattr(evaluation, "is_valid", True)
            feedback = getattr(evaluation, "feedback", "")
        
        if is_valid:
            logger.info("Critic Node: APPROVED.")
            return {"critic_feedback": ""}
        else:
            logger.warning(f"Critic Node: REJECTED. Feedback: {feedback}")
            
            if thread_id:
                await publish_thought(f"stream:{thread_id}", f"\n\n> Critic Rejected Itinerary:\n> {feedback}\n")
            
            # --- THE INTRA-TURN STATE COLLAPSER ---
            # If the critic rejects, we delete the bad final AI message so it can try again
            # WITHOUT wiping the successful tools it used in previous loops.
            drop_commands = []
            if messages and messages[-1].type == "ai":
                if messages[-1].id:
                    drop_commands.append(RemoveMessage(id=messages[-1].id))
            
            return {
                "critic_feedback": f"CRITIC REJECTION: {evaluation.feedback}",
                "retry_count": retry_count + 1,
                "messages": drop_commands # This physically deletes the bad AI response
            }
            
    except Exception as e:
        logger.error(f"Critic Node failed: {e}")
        # If the critic crashes, default to pass
        return {"critic_feedback": ""}
