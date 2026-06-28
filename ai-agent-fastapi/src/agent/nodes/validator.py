from pydantic import ValidationError
from langchain_core.messages import ToolMessage
from src.schemas.agent import AgentState
from src.core.error_handlers import node_error_boundary
import json

def _check_time_overlap(itinerary_draft: dict, day_number: int, arrival_time: str, departure_time: str) -> str:
    if not itinerary_draft or not isinstance(itinerary_draft, dict):
        return ""
    if not arrival_time or not departure_time:
        return ""
        
    days = itinerary_draft.get("days", [])
    target_day = next((d for d in days if d.get("dayNumber") == day_number), None)
    if not target_day:
        return ""
        
    for stop in target_day.get("stops", []):
        existing_arr = stop.get("arrivalTime")
        existing_dep = stop.get("departureTime")
        if not existing_arr or not existing_dep:
            continue
            
        # Basic string comparison works for HH:mm overlaps (e.g. 10:00 < 11:30)
        # New block overlaps if: (new_arr < exist_dep) AND (new_dep > exist_arr)
        if arrival_time < existing_dep and departure_time > existing_arr:
            return f"Time overlap detected on Day {day_number}. Stop '{stop.get('locationName')}' is scheduled from {existing_arr} to {existing_dep}."
            
    return ""

@node_error_boundary
def validate_tool_call(state: AgentState):
    """
    Intercepts Gemini's tool calls BEFORE they execute.
    """
    last_message = state["messages"][-1]
    
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {"validation_error": ""}
        
    bounce_backs = []
    has_error = False
    
    # Import schemas locally to avoid circular imports if any
    from src.agent.tools.draft import DraftAddStopArgs, DraftUpdateStopArgs, DraftMoveStopArgs, DraftAddDayArgs, DraftRemoveDayArgs, DraftRemoveStopArgs
    
    schema_map = {
        "draft_add_stop": DraftAddStopArgs,
        "draft_update_stop": DraftUpdateStopArgs,
        "draft_move_stop": DraftMoveStopArgs,
        "draft_add_day": DraftAddDayArgs,
        "draft_remove_day": DraftRemoveDayArgs,
        "draft_remove_stop": DraftRemoveStopArgs
    }
    
    itinerary_draft = state.get("itinerary_draft", {})
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        error_msg = ""
        
        # 1. Pydantic JSON Validation
        schema = schema_map.get(tool_name)
        if schema:
            try:
                schema(**tool_args)
            except ValidationError as e:
                error_msg = f"Invalid JSON arguments: {str(e)}"
                
        # 2. Deterministic Time Overlap Check
        if not error_msg and tool_name in ["draft_add_stop", "draft_update_stop"]:
            arr = tool_args.get("arrival_time")
            dep = tool_args.get("departure_time")
            day = tool_args.get("day_number")
            if arr and dep and day:
                if arr >= dep:
                    error_msg = "arrival_time must be strictly before departure_time."
                else:
                    overlap = _check_time_overlap(itinerary_draft, day, arr, dep)
                    if overlap:
                        error_msg = overlap

        if error_msg:
            has_error = True
            bounce_backs.append(ToolMessage(
                content=f"Error: {error_msg}",
                tool_call_id=tool_call["id"],
                name=tool_name
            ))
            
    if has_error:
        # We ONLY return ToolMessages for the broken ones.
        # router_from_validator will route to auto_tools to execute the remaining valid ones.
        return {"messages": bounce_backs, "validation_error": "Partial tool failure."}

    return {"validation_error": ""}
