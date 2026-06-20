import os
import grpc
import httpx
from sqlalchemy import text
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Import database engine
from src.core.database import engine

# Import the auto-generated gRPC stubs!
from src.generated import itinerary_pb2
from src.generated import itinerary_pb2_grpc

# 1. The Pydantic Contract
class AddStopArgs(BaseModel):
    trip_id: str = Field(description="The UUID of the trip")
    day_index: int = Field(description="The zero-indexed day to add the stop to (e.g. 0 for Day 1)")
    stop_name: str = Field(description="The name of the location or stop to add")

# 2. The Tool Binding
@tool(args_schema=AddStopArgs)
async def add_stop_to_day(trip_id: str, day_index: int, stop_name: str) -> str:
    """
    Call this tool when the user explicitly asks to add a new location or stop to their itinerary.
    Do NOT call this tool if they are just asking for recommendations.
    """
    print(f"[Agent Tool] Adding '{stop_name}' to Trip {trip_id} (Day {day_index})")
    
    # 1. Resolve day_id from the database
    day_id = None
    try:
        async with engine.begin() as conn:
            # Assuming Java day_number is 1-indexed, we query for day_index + 1
            result = await conn.execute(
                text("SELECT id FROM itinerary.itinerary_day WHERE itinerary_id = CAST(:trip_id AS UUID) AND day_number = :day_number"),
                {"trip_id": trip_id, "day_number": day_index + 1}
            )
            row = result.fetchone()
            if not row:
                return f"Error: Could not find Day {day_index + 1} for Trip {trip_id} in the database."
            day_id = str(row[0])
    except Exception as e:
        return f"Error querying database for day_id: {str(e)}"

    # 2. Resolve Google Place ID using Google Maps API
    google_place_id = None
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY is not configured in the environment."
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/place/findplacefromtext/json",
                params={
                    "input": stop_name,
                    "inputtype": "textquery",
                    "fields": "place_id,name",
                    "key": api_key
                }
            )
            data = response.json()
            if data.get("status") == "OK" and len(data.get("candidates", [])) > 0:
                google_place_id = data["candidates"][0]["place_id"]
            else:
                return f"Error: Could not find a Google Place ID for '{stop_name}'."
    except Exception as e:
        return f"Error querying Google Places API: {str(e)}"

    # 3. The Enterprise gRPC Execution!
    grpc_url = os.getenv("ITINERARY_GRPC_URL", "localhost:9091")
    print(f"Opening async gRPC channel to {grpc_url} with Place ID: {google_place_id} and Day ID: {day_id}")
    
    try:
        # Create an async gRPC channel to the Java microservice
        async with grpc.aio.insecure_channel(grpc_url) as channel:
            # Instantiate the generated stub
            stub = itinerary_pb2_grpc.ItineraryGrpcServiceStub(channel)
            
            # Build the strict Protobuf Request
            request = itinerary_pb2.AddStopGrpcRequest(
                day_id=day_id,
                user_id="test-user-123", # Authentication injection to be handled centrally
                google_place_id=google_place_id,
                stop_type=itinerary_pb2.ATTRACTION,
                user_notes=f"Added by AI Assistant: {stop_name}"
            )
            
            # Execute the gRPC call!
            response = await stub.AddStop(request)
            
            print(f"gRPC Success! Created Stop UUID: {response.id}")
            return f"Successfully added {stop_name} to day {day_index + 1}. The backend returned Stop ID: {response.id}"
            
    except grpc.aio.AioRpcError as e:
        error_msg = f"gRPC call failed with status {e.code()}: {e.details()}"
        print(f"Error: {error_msg}")
        return error_msg