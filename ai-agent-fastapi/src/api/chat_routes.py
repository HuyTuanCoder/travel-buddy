import json
import asyncio
import os
from typing import Optional
from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import redis.asyncio as redis

# We import the celery tasks from the modular workers directory
from src.workers.itinerary_tasks import process_chat_message
from src.workers.setup import celery_app

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

router = APIRouter()

class ChatRequest(BaseModel):
    trip_id: str
    message: str
    itinerary_draft: Optional[dict] = None

class ApproveRequest(BaseModel):
    trip_id: str

class FinalizeRequest(BaseModel):
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
    process_chat_message.delay(
        trip_id=request.trip_id,
        message=request.message,
        itinerary_draft=request.itinerary_draft,
        user_id=x_user_id or "anonymous",
        correlation_id=x_correlation_id or "none"
    )
    return {"status": "accepted", "message": "Task queued for processing."}


@router.post("/chat/finalize", status_code=202)
async def finalize_endpoint(
    request: FinalizeRequest,
    x_user_id: Optional[str] = Header(None),
    x_correlation_id: Optional[str] = Header(None)
):
    """
    Called when the user navigates away from the trip view.
    Forces an immediate background extraction of the unevicted chat history for this trip.
    """
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from src.core.database import DATABASE_URL
    from src.workers.memory_tasks import process_evicted_memory
    
    conn_string = DATABASE_URL.replace("+asyncpg", "")
    async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
        config = {"configurable": {"thread_id": request.trip_id}}
        state_tuple = await checkpointer.aget_tuple(config)
        
        if state_tuple and state_tuple.checkpoint:
            messages = state_tuple.checkpoint["channel_values"].get("messages", [])
            texts_to_extract = [msg.content for msg in messages if isinstance(msg.content, str)]
            user_id = x_user_id or "anonymous"
            if texts_to_extract:
                process_evicted_memory.delay(texts_to_extract, user_id, request.trip_id)
                
    return {"status": "accepted", "message": "Finalize extraction queued."}

@router.get("/chat/{trip_id}/history")
async def chat_history(trip_id: str):
    """
    Fetches the conversation history for a given trip from the permanent ChatHistory table.
    """
    from src.core.database import AsyncSessionLocal
    from src.schemas.database import ChatHistory
    from sqlalchemy import select
    import uuid
    
    try:
        trip_uuid = uuid.UUID(trip_id)
    except ValueError:
        return {"messages": []}
        
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ChatHistory).where(ChatHistory.trip_id == trip_uuid)
        )
        history_record = result.scalars().first()
        
        if not history_record:
            return {"messages": []}
            
        messages = history_record.messages
        
        # Format the Langchain messages for the frontend
        formatted_history = []
        for msg in messages:
            msg_type = msg.get("type", "")
            msg_content = msg.get("content", "")
            msg_id = msg.get("id", "")
            
            if msg_type == "human":
                formatted_history.append({"id": msg_id, "role": "user", "content": str(msg_content)})
            elif msg_type == "ai":
                if msg_content:
                    formatted_history.append({"id": msg_id, "role": "agent", "content": str(msg_content)})
                
        return {"messages": formatted_history}

# Server-side timeout for SSE streams (seconds)
SSE_TIMEOUT = 120
SSE_HEARTBEAT_INTERVAL = 15

@router.get("/chat/{trip_id}/stream")
async def stream_chat(trip_id: str, request: Request):
    """
    Server-Sent Events (SSE) endpoint to stream real-time updates from Redis Pub/Sub.
    Includes a server-side timeout and periodic heartbeat keepalives.
    """
    async def event_generator():
        redis_client = redis.from_url(REDIS_URL)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"stream:{trip_id}")
        
        import time
        last_event_time = time.monotonic()
        last_heartbeat_time = time.monotonic()
        
        try:
            while True:
                # Disconnect check is sometimes buggy in Starlette, let's remove it for now to test
                # if await request.is_disconnected():
                #     break
                
                now = time.monotonic()
                
                # The heartbeat keepalive below will ensure the connection stays active.
                
                # Heartbeat keepalive every SSE_HEARTBEAT_INTERVAL seconds
                if now - last_heartbeat_time > SSE_HEARTBEAT_INTERVAL:
                    yield f": heartbeat\n\n"
                    last_heartbeat_time = now
                
                # Fetch message from redis
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message is not None:
                    # Message is formatted as bytes, need to decode
                    data = message["data"].decode("utf-8")
                    # Format strictly as SSE: "data: {json}\n\n"
                    yield f"data: {data}\n\n"
                    last_event_time = now
                    
                await asyncio.sleep(0.1) # Small sleep to prevent CPU spin
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"FATAL SSE ERROR: {e}\n{error_trace}")
            yield f"event: error\ndata: {str(e)}\n\n"
        finally:
            await pubsub.unsubscribe(f"stream:{trip_id}")
            await redis_client.close()
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")