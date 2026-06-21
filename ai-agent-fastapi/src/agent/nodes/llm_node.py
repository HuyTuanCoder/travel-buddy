import structlog
import os
from langchain_core.messages import SystemMessage
from src.schemas.agent import AgentState
from src.agent.tools.itinerary import add_stop, remove_stop, update_stop, move_stop_between_days
from src.agent.tools.discovery import search_web, read_webpage, find_and_register_place
from src.core.config import get_llm

logger = structlog.get_logger(__name__)

llm = get_llm()

tools = [
    add_stop, remove_stop, update_stop, move_stop_between_days,
    search_web, read_webpage, find_and_register_place
]
llm_with_tools = llm.bind_tools(tools)

def call_gemini(state: AgentState):
    """
    Gate 2: The Executor Agent.
    Executes tools strictly following the Planner's blueprint and addressing any Critic/Validator feedback.
    """
    messages = state.get("messages", [])
    plan = state.get("plan", [])
    critic_feedback = state.get("critic_feedback", "")
    validation_error = state.get("validation_error", "")
    
    # Construct a dynamic System Prompt for execution
    execution_context = "You are an AI Travel Agent Executor.\n"
    
    if plan:
        execution_context += "\nYOUR MANDATORY PLAN (Execute these steps strictly):\n"
        for i, step in enumerate(plan):
            execution_context += f"{i+1}. {step}\n"
            
    if critic_feedback:
        execution_context += f"\nCRITICAL ERROR FROM CRITIC:\n{critic_feedback}\nYou MUST fix this immediately.\n"
        
    if validation_error:
        execution_context += f"\nTOOL VALIDATION ERROR:\n{validation_error}\nYou MUST fix your JSON schema.\n"
        
    # Inject the execution context as a SystemMessage
    sys_msg = SystemMessage(content=execution_context)
    
    # We pass the sys_msg + all conversation messages
    invoke_messages = [sys_msg] + messages

    logger.info("Agent Node: Executing next step...")
    # pass to llm
    response = llm_with_tools.invoke(invoke_messages)

    # Return new messages to be appended to state.
    # Also clear the validation error since we are trying again.
    return {
        "messages": [response],
        "validation_error": ""
    }