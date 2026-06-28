import json
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.core.error_handlers import tool_error_boundary

# 1. Pydantic Contracts

class DraftAddStopArgs(BaseModel):
    day_number: int = Field(description="The 1-indexed day number to add the stop to (e.g. 1 for Day 1)")
    google_place_id: str = Field(description="The Google Place ID of the location to add. Must be obtained via find_and_register_place.")
    name: str = Field(description="The name of the place (e.g. 'Hyatt Regency')")
    stop_type: str = Field(description="The category of the stop. Allowed values: ATTRACTION, RESTAURANT, LODGING, TRANSIT, UNKNOWN")
    user_notes: str = Field(default="", description="Optional notes or context about this stop for the user")
    arrival_time: str = Field(default="", description="Optional planned arrival time in HH:mm format")
    departure_time: str = Field(default="", description="Optional planned departure time in HH:mm format")
    estimated_cost: str = Field(default="", description="Optional estimated cost as a decimal string")

class DraftRemoveStopArgs(BaseModel):
    google_place_id: str = Field(description="The Google Place ID of the stop to remove from the draft.")
    day_number: int = Field(description="The day number the stop is currently on.")

class DraftAddDayArgs(BaseModel):
    scheduled_date: str = Field(default="", description="Optional date for the new day in YYYY-MM-DD format.")

class DraftRemoveDayArgs(BaseModel):
    day_number: int = Field(description="The day number to completely remove.")

# 2. Tool Bindings

@tool("draft_add_stop", args_schema=DraftAddStopArgs)
@tool_error_boundary
def draft_add_stop(day_number: int, google_place_id: str, name: str, stop_type: str, user_notes: str = "", arrival_time: str = "", departure_time: str = "", estimated_cost: str = "") -> str:
    """
    Call this tool to incrementally build the user's itinerary DRAFT in memory.
    This does NOT hit the database. It simply formats the stop as a JSON string to be appended to the state.
    """
    draft_item = {
        "action": "add",
        "day_number": day_number,
        "google_place_id": google_place_id,
        "name": name,
        "stop_type": stop_type,
        "user_notes": user_notes,
        "arrival_time": arrival_time,
        "departure_time": departure_time,
        "estimated_cost": estimated_cost
    }
    return json.dumps(draft_item)

class DraftUpdateStopArgs(BaseModel):
    google_place_id: str = Field(description="The Google Place ID of the stop to update.")
    day_number: int = Field(description="The day number the stop is currently on.")
    user_notes: str = Field(default="", description="Optional updated notes")
    arrival_time: str = Field(default="", description="Optional updated arrival time (HH:mm)")
    departure_time: str = Field(default="", description="Optional updated departure time (HH:mm)")
    estimated_cost: str = Field(default="", description="Optional updated estimated cost")

class DraftMoveStopArgs(BaseModel):
    google_place_id: str = Field(description="The Google Place ID of the stop to move.")
    old_day_number: int = Field(description="The day number the stop is currently on.")
    new_day_number: int = Field(description="The day number to move the stop to.")
    new_visit_order: int = Field(default=None, description="Optional. The exact 0-indexed position to place the stop in the new day. If moving within the same day, use this to reorder.")

@tool("draft_remove_stop", args_schema=DraftRemoveStopArgs)
@tool_error_boundary
def draft_remove_stop(google_place_id: str, day_number: int) -> str:
    """
    Call this tool to remove a stop from the user's itinerary DRAFT in memory.
    """
    draft_item = {
        "action": "remove",
        "google_place_id": google_place_id,
        "day_number": day_number
    }
    return json.dumps(draft_item)

@tool("draft_update_stop", args_schema=DraftUpdateStopArgs)
@tool_error_boundary
def draft_update_stop(google_place_id: str, day_number: int, user_notes: str = "", arrival_time: str = "", departure_time: str = "", estimated_cost: str = "") -> str:
    """
    Call this tool to update the notes or timings of an existing stop in the itinerary DRAFT in memory.
    """
    draft_item = {
        "action": "update",
        "google_place_id": google_place_id,
        "day_number": day_number,
        "user_notes": user_notes,
        "arrival_time": arrival_time,
        "departure_time": departure_time,
        "estimated_cost": estimated_cost
    }
    return json.dumps(draft_item)

@tool("draft_move_stop", args_schema=DraftMoveStopArgs)
@tool_error_boundary
def draft_move_stop(google_place_id: str, old_day_number: int, new_day_number: int, new_visit_order: int = None) -> str:
    """
    Call this tool to move a stop across days OR reorder it within the same day.
    """
    draft_item = {
        "action": "move",
        "google_place_id": google_place_id,
        "old_day_number": old_day_number,
        "new_day_number": new_day_number
    }
    if new_visit_order is not None:
        draft_item["new_visit_order"] = new_visit_order
    return json.dumps(draft_item)

@tool("draft_add_day", args_schema=DraftAddDayArgs)
@tool_error_boundary
def draft_add_day(scheduled_date: str = "") -> str:
    """
    Call this tool to append a new day to the itinerary DRAFT.
    """
    return json.dumps({
        "action": "add_day",
        "scheduled_date": scheduled_date
    })

@tool("draft_remove_day", args_schema=DraftRemoveDayArgs)
@tool_error_boundary
def draft_remove_day(day_number: int) -> str:
    """
    Call this tool to remove an entire day and its stops from the itinerary DRAFT.
    """
    return json.dumps({
        "action": "remove_day",
        "day_number": day_number
    })
