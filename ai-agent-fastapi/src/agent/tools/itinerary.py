from langchain_core.tools import tool

@tool
def add_stop_to_day(trip_id: str, day: int, location_name:str, time: str) -> str:
    """Use this tool to add a new stop to the user's travel itinerary."""
    print(f"--> [JAVA API MOCK] Adding {location_name} to Trip {trip_id} on Day {day} at {time}...")
    
    return f"Successfully added {location_name} to the itinerary."