import json
from langchain_core.tools import tool
from pydantic import BaseModel, Field

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

# 2. Tool Bindings

@tool("draft_add_stop", args_schema=DraftAddStopArgs)
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

@tool("draft_remove_stop", args_schema=DraftRemoveStopArgs)
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
