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
    day_number: int = Field(description="The 1-indexed day number to add (e.g. 1 for Day 1). Must be provided explicitly.")
    scheduled_date: str = Field(default="", description="Optional date for the new day in YYYY-MM-DD format.")

class DraftRemoveDayArgs(BaseModel):
    day_number: int = Field(description="The day number to completely remove.")

class DraftRestoreDayArgs(BaseModel):
    day_number: int = Field(description="The day number to restore from a ghosted (soft-deleted) state.")

class DraftRestoreStopArgs(BaseModel):
    google_place_id: str = Field(description="The Google Place ID of the stop to restore.")
    day_number: int = Field(description="The day number the stop was on when removed.")

class DraftSwapDaysArgs(BaseModel):
    day_a: int = Field(description="The 1-indexed day number of the first day to swap.")
    day_b: int = Field(description="The 1-indexed day number of the second day to swap.")

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
        "is_draft": True,
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
    Call this tool to remove a stop from the itinerary DRAFT.
    Note: This performs a soft-delete (tombstone). The item is ghosted in the UI.
    """
    draft_item = {
        "action": "remove",
        "is_draft": True,
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
        "is_draft": True,
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
    IMPORTANT: If the user is ambiguous (e.g., 'move this to the first day' but doesn't specify exact order), leave new_visit_order as null. The frontend will safely append it to the end of that day.
    """
    draft_item = {
        "action": "move",
        "is_draft": True,
        "google_place_id": google_place_id,
        "old_day_number": old_day_number,
        "new_day_number": new_day_number
    }
    if new_visit_order is not None:
        draft_item["new_visit_order"] = new_visit_order
    return json.dumps(draft_item)

@tool("draft_add_day", args_schema=DraftAddDayArgs)
@tool_error_boundary
def draft_add_day(day_number: int, scheduled_date: str = "") -> str:
    """
    Call this tool to explicitly add a new day to the itinerary DRAFT.
    """
    return json.dumps({
        "action": "add_day",
        "is_draft": True,
        "day_number": day_number,
        "scheduled_date": scheduled_date
    })

@tool("draft_remove_day", args_schema=DraftRemoveDayArgs)
@tool_error_boundary
def draft_remove_day(day_number: int) -> str:
    """
    Call this tool to remove an entire day and its stops from the itinerary DRAFT.
    Note: This performs a soft-delete (tombstone). The day is ghosted in the UI.
    """
    return json.dumps({
        "action": "remove_day",
        "is_draft": True,
        "day_number": day_number
    })

@tool("draft_restore_day", args_schema=DraftRestoreDayArgs)
@tool_error_boundary
def draft_restore_day(day_number: int) -> str:
    """
    Use this to undo the removal of a day. The frontend will un-ghost it.
    Example: User says 'Actually, put Day 3 back', call draft_restore_day(day_number=3)
    """
    return json.dumps({
        "action": "restore_day",
        "is_draft": True,
        "day_number": day_number
    })

@tool("draft_restore_stop", args_schema=DraftRestoreStopArgs)
@tool_error_boundary
def draft_restore_stop(google_place_id: str, day_number: int) -> str:
    """
    Use this to undo the removal of a stop.
    Example: User says 'Wait, add back the Louvre', call draft_restore_stop(google_place_id='ChIJ...', day_number=2)
    """
    return json.dumps({
        "action": "restore_stop",
        "is_draft": True,
        "google_place_id": google_place_id,
        "day_number": day_number
    })

@tool("draft_swap_days", args_schema=DraftSwapDaysArgs)
@tool_error_boundary
def draft_swap_days(day_a: int, day_b: int) -> str:
    """
    Use this to completely swap the schedule of two days.
    Example: User says 'Switch my Tuesday and Wednesday', call draft_swap_days(day_a=2, day_b=3)
    """
    return json.dumps({
        "action": "swap_days",
        "is_draft": True,
        "day_a": day_a,
        "day_b": day_b
    })
