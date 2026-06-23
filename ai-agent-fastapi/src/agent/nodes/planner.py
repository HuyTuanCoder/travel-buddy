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

def plan_itinerary(state: AgentState, config: dict):
    """
    Gate 1: The Planner Node.
    Forces the AI to generate a strict reasoning trace before executing tools.
    """
    import redis
    import json
    from src.core.config import settings
    
    thread_id = config.get("configurable", {}).get("thread_id", "")
    if thread_id:
        try:
            r = redis.from_url(settings.REDIS_URL)
            r.publish(f"stream:{thread_id}", json.dumps({
                "type": "thought",
                "content": "Analyzing request constraints and building step-by-step checklist..."
            }))
        except Exception as e:
            logger.error(f"Failed to publish thought: {e}")

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
    
    # Extract the RAG context and the current draft from the state
    rag_context = state.get("rag_context", "")
    itinerary_draft = state.get("itinerary_draft", [])
    import json
    draft_context = json.dumps(itinerary_draft, indent=2) if itinerary_draft else "The draft is currently empty."
            
    system_prompt = f"""
    You are the Master Itinerary Planner. 
    Your job is to read the user's request, the known constraints, and the CURRENT ITINERARY DRAFT, and generate a strict, linear checklist of actions for an executor agent to follow.
    
    Known Constraints & Memories:
    {rag_context}
    
    CURRENT ITINERARY DRAFT:
    {draft_context}
    
    CRITICAL PLANNING RULES:
    1. VAGUE REQUESTS: If the user simply says "Plan a trip to X" with no dates, budget, or preferences, DO NOT generate a plan to build the itinerary. Instead, output a plan to: "Ask the user clarifying questions about dates, budget, and dietary preferences."
    2. THE DRAFT STATE: The Agent maintains an in-memory `itinerary_draft`. You must instruct the agent to build the trip incrementally into this draft. Do NOT instruct the agent to call database tools (`add_stop`) until the user explicitly says "Build this" or "I approve the draft".
    3. REAL-TIME DISCOVERY: Actively encourage the agent to use `search_web` to discover "what is currently popular" or "hidden gems".
    4. PARALLEL EXECUTION (AVOID CRASHES): The Agent MUST execute tools simultaneously whenever possible. If you need to find 5 places, instruct the Agent to call `find_and_register_place` 5 times in a single JSON payload.
    5. CONVERSATIONAL PUSHBACK (HARD LIMIT): Never instruct the Agent to draft an entire multi-day trip at once. It will crash the system. Instruct the Agent: "Never draft more than 3 to 5 stops (1 day) at a time. Once you hit this limit, you MUST stop execution, present the draft, and ask the user to check the itinerary panel for approval."
    
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
        
        if hasattr(plan_output, 'steps'):
            steps = plan_output.steps
        elif isinstance(plan_output, list) and len(plan_output) > 0 and isinstance(plan_output[0], dict):
            # Handle langchain-google-vertexai 1.0.4 returning raw OpenAI tool schema format
            steps = plan_output[0].get("args", {}).get("steps", [])
        else:
            steps = []
            
        if thread_id and steps:
            try:
                formatted_steps = "\n> ".join(steps)
                r = redis.from_url(settings.REDIS_URL)
                r.publish(f"stream:{thread_id}", json.dumps({
                    "type": "thought",
                    "content": f"\n\n> Created Execution Plan:\n> {formatted_steps}\n"
                }))
            except Exception as e:
                logger.error(f"Failed to publish thought: {e}")
        
        # Reset retry_count on new plan
        return {
            "plan": steps,
            "retry_count": 0,
            "critic_feedback": ""
        }
    except Exception as e:
        logger.error(f"Planner Node failed: {e}")
        return {"plan": ["Acknowledge user request.", "Proceed with default execution."]}
