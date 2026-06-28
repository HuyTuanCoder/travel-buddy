import structlog
import os
from langchain_core.messages import SystemMessage
from src.schemas.agent import AgentState

from src.agent.tools.discovery import search_web, read_webpage, find_and_register_place
from src.agent.tools.memory import search_past_conversations
from src.agent.tools.draft import (
    draft_add_stop, draft_remove_stop, draft_update_stop, draft_move_stop, 
    draft_add_day, draft_remove_day, draft_restore_day, draft_restore_stop, draft_swap_days
)
from src.core.config import get_llm
import json
from langchain_core.runnables import RunnableConfig
from src.core.error_handlers import node_error_boundary

logger = structlog.get_logger(__name__)

ALL_TOOLS = [
    search_web, read_webpage, find_and_register_place, search_past_conversations,
    draft_add_stop, draft_remove_stop, draft_update_stop, draft_move_stop, 
    draft_add_day, draft_remove_day, draft_restore_day, draft_restore_stop, draft_swap_days
]

@node_error_boundary
async def call_executor(state: AgentState, config: RunnableConfig):
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
    itinerary_draft = state.get("itinerary_draft", {})
    if not isinstance(itinerary_draft, dict):
        itinerary_draft = {}
    if "days" not in itinerary_draft:
        itinerary_draft["days"] = []
    
    # Process all ToolMessages that were just added
    recent_tools = []
    for msg in reversed(messages):
        if msg.type == "tool":
            recent_tools.append(msg)
        elif msg.type == "ai":
            break
            
    recent_tools.reverse() # Process in chronological order
    
    for tool_msg in recent_tools:
        if tool_msg.name in ["draft_add_stop", "draft_remove_stop", "draft_update_stop", "draft_move_stop", "draft_add_day", "draft_remove_day"]:
            content_str = str(tool_msg.content)
            # If the tool failed validation or crashed, it returns a [System] string. Skip parsing.
            if content_str.startswith("[System]") or content_str.startswith("Error:"):
                continue
                
            action_data = json.loads(content_str)
            action = action_data.get("action")
            
            if action == "add_day":
                next_day = len(itinerary_draft["days"]) + 1
                itinerary_draft["days"].append({"dayNumber": next_day, "stops": []})
            
            elif action == "remove_day":
                itinerary_draft["days"] = [d for d in itinerary_draft["days"] if d.get("dayNumber") != action_data.get("day_number")]
            
            elif action == "add":
                day_num = action_data.get("day_number")
                day = next((d for d in itinerary_draft["days"] if d.get("dayNumber") == day_num), None)
                if day is not None:
                    day.setdefault("stops", []).append({
                        "googlePlaceId": action_data.get("google_place_id"),
                        "locationName": action_data.get("name"),
                        "category": action_data.get("stop_type"),
                        "arrivalTime": action_data.get("arrival_time"),
                        "departureTime": action_data.get("departure_time")
                    })
            
            elif action == "remove":
                day_num = action_data.get("day_number")
                place_id = action_data.get("google_place_id")
                day = next((d for d in itinerary_draft["days"] if d.get("dayNumber") == day_num), None)
                if day is not None and "stops" in day:
                    day["stops"] = [s for s in day["stops"] if s.get("googlePlaceId") != place_id]
            
            elif action == "update":
                day_num = action_data.get("day_number")
                place_id = action_data.get("google_place_id")
                day = next((d for d in itinerary_draft["days"] if d.get("dayNumber") == day_num), None)
                if day is not None:
                    for stop in day.get("stops", []):
                        if stop.get("googlePlaceId") == place_id:
                            if action_data.get("arrival_time"):
                                stop["arrivalTime"] = action_data["arrival_time"]
                            if action_data.get("departure_time"):
                                stop["departureTime"] = action_data["departure_time"]
            
            elif action == "move":
                old_day_num = action_data.get("old_day_number")
                new_day_num = action_data.get("new_day_number")
                place_id = action_data.get("google_place_id")
                new_order = action_data.get("new_visit_order")
                
                old_day = next((d for d in itinerary_draft["days"] if d.get("dayNumber") == old_day_num), None)
                new_day = next((d for d in itinerary_draft["days"] if d.get("dayNumber") == new_day_num), None)
                
                if old_day and new_day and "stops" in old_day:
                    target_stop = next((s for s in old_day["stops"] if s.get("googlePlaceId") == place_id), None)
                    if target_stop:
                        old_day["stops"] = [s for s in old_day["stops"] if s.get("googlePlaceId") != place_id]
                        if new_order is not None and new_order < len(new_day.setdefault("stops", [])):
                            new_day["stops"].insert(new_order, target_stop)
                        else:
                            new_day.setdefault("stops", []).append(target_stop)
    
    # Construct a static System Prompt for identity
    sys_msg = SystemMessage(content="""You are an AI Travel Agent Executor.
    
    IMPORTANT MANDATE:
    If the user's request is ambiguous (e.g., 'move it to the start' but you don't know which exact order, or 'swap that day' but you don't know which two days), DO NOT GUESS and DO NOT CALL TOOLS. 
    Instead, output a natural language question asking the user to clarify exactly where they want it.""")
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