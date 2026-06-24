import structlog
import os
from langchain_core.messages import SystemMessage
from src.schemas.agent import AgentState
from src.agent.tools.itinerary import add_stop, remove_stop, update_stop, move_stop_between_days
from src.agent.tools.discovery import search_web, read_webpage, find_and_register_place
from src.agent.tools.memory import search_past_conversations
from src.agent.tools.draft import draft_add_stop, draft_remove_stop
from src.core.config import get_llm
import json

logger = structlog.get_logger(__name__)

ALL_TOOLS = [
    add_stop, remove_stop, update_stop, move_stop_between_days,
    search_web, read_webpage, find_and_register_place, search_past_conversations,
    draft_add_stop, draft_remove_stop
]

async def call_gemini(state: AgentState, config: dict):
    # Instantiate LLM inside the function to avoid gRPC event loop binding issues in Celery prefork workers.
    # planner.py and critic.py already do this correctly.
    llm = get_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
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
    
    # Construct a static System Prompt for identity
    sys_msg = SystemMessage(content="You are an AI Travel Agent Executor.")
    
    # Construct an ephemeral context injection for the BOTTOM of the prompt
    ephemeral_context = "\n--- SYSTEM EXECUTION CONTEXT ---\n"
    
    rag_context = state.get("rag_context", "")
    if rag_context:
        ephemeral_context += f"\nKNOWN CONSTRAINTS & MEMORIES:\n{rag_context}\n"
        
    running_summary = state.get("running_summary", "")
    if running_summary:
        ephemeral_context += f"\nPREVIOUS EVENTS (Summary of dropped messages):\n{running_summary}\n"
        
    if itinerary_draft:
        ephemeral_context += f"\nYOUR CURRENT ITINERARY DRAFT (In Memory):\n{json.dumps(itinerary_draft, indent=2)}\n"
    
    if plan:
        ephemeral_context += "\nYOUR MANDATORY PLAN (Execute these steps strictly. NEVER draft more than 3-5 stops at a time):\n"
        for i, step in enumerate(plan):
            ephemeral_context += f"{i+1}. {step}\n"
            
    if critic_feedback:
        ephemeral_context += f"\nCRITICAL ERROR FROM CRITIC:\n{critic_feedback}\nYou MUST fix this immediately.\n"
        
    if validation_error:
        ephemeral_context += f"\nTOOL VALIDATION ERROR:\n{validation_error}\nYou MUST fix your JSON schema.\n"
    
    ephemeral_context += "\nRead the chat history above, then execute the next step of your plan based on the constraints."
        
    # Filter out any other SystemMessages (like from RAG) to prevent Gemini crashes
    filtered_history = [msg for msg in messages if not isinstance(msg, SystemMessage)]
    
    # Append the ephemeral context as a final HumanMessage to defeat "Lost in the Middle"
    from langchain_core.messages import HumanMessage
    invoke_messages = [sys_msg] + filtered_history + [HumanMessage(content=ephemeral_context)]

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