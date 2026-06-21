import json
import asyncio
import os
from typing import Optional
from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import redis.asyncio as redis

# We import the celery tasks from the modular workers directory
from src.workers.itinerary_tasks import process_chat_message, approve_tool_call

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

router = APIRouter()

class ChatRequest(BaseModel):
    trip_id: str
    message: str

class ApproveRequest(BaseModel):
    trip_id: str

@router.post("/chat", status_code=202)
async def chat_endpoint(
    request: ChatRequest,
    x_user_id: Optional[str] = Header(None),
    x_correlation_id: Optional[str] = Header(None)
):
    """
    Offloads the chat request to RabbitMQ via Celery and returns immediately.
    We leverage the Spring API Gateway injected headers for distributed tracing/auth.
    """
    # .delay() pushes this to RabbitMQ instantly
    process_chat_message.delay(
        trip_id=request.trip_id,
        message=request.message,
        user_id=x_user_id or "anonymous",
        correlation_id=x_correlation_id or "none"
    )
    return {"status": "accepted", "message": "Task queued for processing."}

@router.post("/chat/approve", status_code=202)
async def approve_endpoint(
    request: ApproveRequest,
    x_user_id: Optional[str] = Header(None),
    x_correlation_id: Optional[str] = Header(None)
):
    """
    Resumes a paused LangGraph execution by offloading the task to RabbitMQ.
    """
    approve_tool_call.delay(
        trip_id=request.trip_id,
        user_id=x_user_id or "anonymous",
        correlation_id=x_correlation_id or "none"
    )
    return {"status": "accepted", "message": "Approval task queued for processing."}

@router.get("/chat/{trip_id}/stream")
async def stream_chat(trip_id: str, request: Request):
    """
    Server-Sent Events (SSE) endpoint to stream real-time updates from Redis Pub/Sub.
    Because this is standard HTTP GET, Spring Cloud Gateway proxies it natively.
    """
    async def event_generator():
        redis_client = redis.from_url(REDIS_URL)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"stream:{trip_id}")
        
        try:
            while True:
                # Disconnect if client dropped connection (e.g. closed browser)
                if await request.is_disconnected():
                    break
                
                # Fetch message from redis
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message is not None:
                    # Message is formatted as bytes, need to decode
                    data = message["data"].decode("utf-8")
                    # Format strictly as SSE: "data: {json}\n\n"
                    yield f"data: {data}\n\n"
                    
                await asyncio.sleep(0.1) # Small sleep to prevent CPU spin
        finally:
            await pubsub.unsubscribe(f"stream:{trip_id}")
            await redis_client.close()
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")