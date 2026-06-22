import structlog
import os
from langchain_core.messages import SystemMessage
from src.schemas.agent import AgentState
from src.agent.tools.itinerary import add_stop, remove_stop, update_stop, move_stop_between_days
from src.agent.tools.discovery import search_web, read_webpage, find_and_register_place
from src.agent.tools.draft import draft_add_stop, draft_remove_stop
from src.core.config import get_llm
import json

logger = structlog.get_logger(__name__)

llm = get_llm()

tools = [
    add_stop, remove_stop, update_stop, move_stop_between_days,
]
llm_with_tools = llm.bind_tools(tools)

async def call_gemini(state: AgentState, config: dict):
    """
    Gate 2: The Executor Agent.
    Executes tools strictly following the Planner's blueprint and addressing any Critic/Validator feedback.
    """
    messages = state.get("messages", [])
    plan = state.get("plan", [])
    critic_feedback = state.get("critic_feedback", "")
    validation_error = state.get("validation_error", "")
    itinerary_draft = state.get("itinerary_draft", [])
    
    # Check if the last message was a ToolMessage from our draft tools.
    # If so, we parse it and append/remove from the local itinerary_draft state.
    if messages and messages[-1].type == "tool":
        last_tool_msg = messages[-1]
        if last_tool_msg.name in ["draft_add_stop", "draft_remove_stop"]:
            try:
                action_data = json.loads(last_tool_msg.content)
                if action_data.get("action") == "add":
                    # Remove the 'action' key and append
                    del action_data["action"]
                    itinerary_draft.append(action_data)
                    logger.info(f"Agent Node: Appended to itinerary_draft. Current draft size: {len(itinerary_draft)}")
                elif action_data.get("action") == "remove":
                    itinerary_draft = [
                        stop for stop in itinerary_draft 
                        if not (stop.get("google_place_id") == action_data.get("google_place_id") and stop.get("day_number") == action_data.get("day_number"))
                    ]
            except Exception as e:
                logger.error(f"Agent Node failed to parse draft tool output: {e}")
    
    # Construct a dynamic System Prompt for execution
    execution_context = "You are an AI Travel Agent Executor.\n"
    
    if itinerary_draft:
        execution_context += f"\nYOUR CURRENT ITINERARY DRAFT (In Memory):\n{json.dumps(itinerary_draft, indent=2)}\n"
    
    if plan:
        execution_context += "\nYOUR MANDATORY PLAN (Execute these steps strictly):\n"
        for i, step in enumerate(plan):
            execution_context += f"{i+1}. {step}\n"
            
    if critic_feedback:
        execution_context += f"\nCRITICAL ERROR FROM CRITIC:\n{critic_feedback}\nYou MUST fix this immediately.\n"
        
    if validation_error:
        execution_context += f"\nTOOL VALIDATION ERROR:\n{validation_error}\nYou MUST fix your JSON schema.\n"
        
    # Inject the execution context as a single SystemMessage
    sys_msg = SystemMessage(content=execution_context)
    
    # Filter out any other SystemMessages (like from RAG) to prevent Gemini crashes
    # Gemini requires exactly one SystemMessage, strictly at the beginning of the history.
    filtered_history = [msg for msg in messages if not isinstance(msg, SystemMessage)]
    
    invoke_messages = [sys_msg] + filtered_history

    logger.info("Agent Node: Executing next step...")
    # pass to llm using ainvoke so LangGraph can stream chunks
    response = await llm_with_tools.ainvoke(invoke_messages, config)

    # Return new messages to be appended to state.
    # Also clear the validation error since we are trying again.
    # Return new messages to be appended to state, and the updated draft!
    return {
        "messages": [response],
        "validation_error": "",
        "itinerary_draft": itinerary_draft
    }