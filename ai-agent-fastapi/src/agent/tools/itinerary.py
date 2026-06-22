import os
import grpc
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.generated import itinerary_pb2
from src.generated import itinerary_pb2_grpc

# 1. Pydantic Contracts

class AddStopArgs(BaseModel):
    trip_id: str = Field(description="The UUID of the itinerary/trip")
    day_number: int = Field(description="The 1-indexed day number to add the stop to (e.g. 1 for Day 1)")
    google_place_id: str = Field(description="The Google Place ID of the location to add. Must be obtained by calling find_and_register_place first.")
    stop_type: str = Field(description="The category of the stop. Allowed values: ATTRACTION, RESTAURANT, LODGING, TRANSIT, UNKNOWN")
    user_notes: str = Field(default="", description="Optional notes or context about this stop for the user")
    arrival_time: str = Field(default="", description="Optional planned arrival time in HH:mm format")
    departure_time: str = Field(default="", description="Optional planned departure time in HH:mm format")
    estimated_cost: str = Field(default="", description="Optional estimated cost as a decimal string")

class RemoveStopArgs(BaseModel):
    stop_id: str = Field(description="The UUID of the stop to remove")

class UpdateStopArgs(BaseModel):
    stop_id: str = Field(description="The UUID of the stop to update")
    stop_type: str = Field(default="UNKNOWN", description="The category of the stop. Allowed values: ATTRACTION, RESTAURANT, LODGING, TRANSIT, UNKNOWN")
    user_notes: str = Field(default="", description="Optional notes or context about this stop for the user")
    arrival_time: str = Field(default="", description="Optional planned arrival time in HH:mm format")
    departure_time: str = Field(default="", description="Optional planned departure time in HH:mm format")
    estimated_cost: str = Field(default="", description="Optional estimated cost as a decimal string")

class MoveStopArgs(BaseModel):
    trip_id: str = Field(description="The UUID of the itinerary/trip")
    stop_id: str = Field(description="The UUID of the stop to move")
    target_day_number: int = Field(description="The 1-indexed day number to move the stop to (e.g. 2 for Day 2)")

# Helper to map string stop_type to enum
def map_stop_type(stop_type_str: str) -> int:
    stop_type_upper = stop_type_str.upper()
    if hasattr(itinerary_pb2, stop_type_upper):
        return getattr(itinerary_pb2, stop_type_upper)
    return itinerary_pb2.UNKNOWN

def get_grpc_url() -> str:
    # Use internal docker compose hostname
    return os.getenv("ITINERARY_GRPC_URL", "itinerary-service:9090")

# 2. Tool Bindings

@tool("add_stop", args_schema=AddStopArgs)
async def add_stop(trip_id: str, day_number: int, google_place_id: str, stop_type: str, user_notes: str = "", arrival_time: str = "", departure_time: str = "", estimated_cost: str = "") -> str:
    """
    Call this tool when the user explicitly asks to add a new location or stop to their itinerary.
    """
    try:
        async with grpc.aio.insecure_channel(get_grpc_url()) as channel:
            stub = itinerary_pb2_grpc.ItineraryGrpcServiceStub(channel)
            request = itinerary_pb2.AddStopGrpcRequest(
                trip_id=trip_id,
                day_number=day_number,
                user_id="test-user-123", # Authentication injected centrally later
                google_place_id=google_place_id,
                stop_type=map_stop_type(stop_type),
                user_notes=user_notes,
                arrival_time=arrival_time,
                departure_time=departure_time,
                estimated_cost=estimated_cost
            )
            response = await stub.AddStop(request)
            return f"Successfully added stop. Backend returned Stop ID: {response.id}, Order: {response.visit_order}"
    except grpc.aio.AioRpcError as e:
        return f"gRPC Error {e.code()}: {e.details()}"

@tool("remove_stop", args_schema=RemoveStopArgs)
async def remove_stop(stop_id: str) -> str:
    """
    Call this tool when the user explicitly asks to remove or delete an existing stop from their itinerary.
    """
    try:
        async with grpc.aio.insecure_channel(get_grpc_url()) as channel:
            stub = itinerary_pb2_grpc.ItineraryGrpcServiceStub(channel)
            request = itinerary_pb2.RemoveStopGrpcRequest(
                stop_id=stop_id,
                user_id="test-user-123"
            )
            await stub.RemoveStop(request)
            return f"Successfully removed stop {stop_id}."
    except grpc.aio.AioRpcError as e:
        return f"gRPC Error {e.code()}: {e.details()}"

@tool("update_stop", args_schema=UpdateStopArgs)
async def update_stop(stop_id: str, stop_type: str = "UNKNOWN", user_notes: str = "", arrival_time: str = "", departure_time: str = "", estimated_cost: str = "") -> str:
    """
    Call this tool when the user asks to update the metadata (like times, notes, or cost) of an existing stop.
    Do NOT use this tool to move a stop to another day.
    """
    try:
        async with grpc.aio.insecure_channel(get_grpc_url()) as channel:
            stub = itinerary_pb2_grpc.ItineraryGrpcServiceStub(channel)
            request = itinerary_pb2.UpdateStopGrpcRequest(
                stop_id=stop_id,
                user_id="test-user-123",
                stop_type=map_stop_type(stop_type),
                user_notes=user_notes,
                arrival_time=arrival_time,
                departure_time=departure_time,
                estimated_cost=estimated_cost
            )
            response = await stub.UpdateStop(request)
            return f"Successfully updated stop {response.id}."
    except grpc.aio.AioRpcError as e:
        return f"gRPC Error {e.code()}: {e.details()}"

@tool("move_stop_between_days", args_schema=MoveStopArgs)
async def move_stop_between_days(trip_id: str, stop_id: str, target_day_number: int) -> str:
    """
    Call this tool when the user asks to move an existing stop from one day to a different day in the itinerary.
    """
    try:
        async with grpc.aio.insecure_channel(get_grpc_url()) as channel:
            stub = itinerary_pb2_grpc.ItineraryGrpcServiceStub(channel)
            request = itinerary_pb2.MoveStopGrpcRequest(
                stop_id=stop_id,
                trip_id=trip_id,
                target_day_number=target_day_number,
                user_id="test-user-123"
            )
            response = await stub.MoveStop(request)
            return f"Successfully moved stop to Day {target_day_number}. Backend returned new Stop ID: {response.id}, Order: {response.visit_order}"
    except grpc.aio.AioRpcError as e:
        return f"gRPC Error {e.code()}: {e.details()}"