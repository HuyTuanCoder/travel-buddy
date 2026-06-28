import functools
import json
import uuid
import structlog
import pydantic
import requests
import grpc
from typing import Callable, Any

from sqlalchemy import text
from src.core.database import AsyncSessionLocal
from src.exceptions.base import TravelBuddyError
from src.exceptions.tools import ToolExecutionError, ToolAPIError, ToolValidationError
from src.exceptions.agent import AgentSystemError, LLMCoreError, GraphStateError
from src.core.streamer import AgentStreamer

logger = structlog.get_logger(__name__)

def tool_error_boundary(func: Callable) -> Callable:
    """
    Wraps Langchain @tool definitions to strictly categorize exceptions,
    log them appropriately, and return an agent-friendly error string for self-correction.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except pydantic.ValidationError as e:
            # The LLM hallucinated bad arguments. This is a normal validation error.
            logger.warning(f"Tool Validation Error in {func.__name__}", exc_info=True)
            return f"[System] Validation Error in {func.__name__}: {str(e)}. Correct your JSON arguments and try again."
        except (requests.RequestException, TimeoutError, ConnectionError, grpc.RpcError):
            # The external dependency is down.
            logger.error(f"Tool API Error in {func.__name__}", exc_info=True)
            return f"[System] Fatal API Error in {func.__name__}. The external service is currently unreachable. Do NOT attempt to call this tool again. Synthesize a response with the information you have, or apologize."
        except Exception as e:
            # Unknown failure
            logger.error(f"Unknown Tool Failure in {func.__name__}", exc_info=True)
            return f"Error executing {func.__name__}: {str(e)}"
    
    # Langchain @tool requires async boundaries for async tools
    @functools.wraps(func)
    async def awrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except pydantic.ValidationError as e:
            logger.warning(f"Tool Validation Error in {func.__name__}", exc_info=True)
            return f"[System] Validation Error in {func.__name__}: {str(e)}. Correct your JSON arguments and try again."
        except (requests.RequestException, TimeoutError, ConnectionError, grpc.RpcError):
            logger.error(f"Tool API Error in {func.__name__}", exc_info=True)
            return f"[System] Fatal API Error in {func.__name__}. The external service is currently unreachable. Do NOT attempt to call this tool again. Synthesize a response with the information you have, or apologize."
        except Exception as e:
            logger.error(f"Unknown Tool Failure in {func.__name__}", exc_info=True)
            return f"Error executing {func.__name__}: {str(e)}"

    return awrapper if getattr(func, "is_coroutine_function", False) or __import__('asyncio').iscoroutinefunction(func) else wrapper


def node_error_boundary(func: Callable) -> Callable:
    """
    Wraps LangGraph nodes. Catches node-level execution crashes (like validator failures)
    and maps them to GraphStateError to halt the graph gracefully.
    """
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Node Execution Crashed: {func.__name__}", exc_info=True)
            raise GraphStateError(f"Node {func.__name__} crashed", original_exception=e)

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Node Execution Crashed: {func.__name__}", exc_info=True)
            raise GraphStateError(f"Node {func.__name__} crashed", original_exception=e)
            
    import asyncio
    if getattr(func, "is_coroutine_function", False) or asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def celery_agent_boundary(func: Callable) -> Callable:
    """
    The outermost Celery boundary. 
    Guarantees the atomic UI Database transaction and Network PubSub streaming,
    no matter what fatal errors bubble up from the agent.
    """
    @functools.wraps(func)
    async def wrapper(trip_id: str, message: str, user_id: str, correlation_id: str, itinerary_draft: dict = None, *args, **kwargs):
        log = logger.bind(thread_id=trip_id, user_id=user_id, correlation_id=correlation_id)
        pubsub_channel = f"stream:{trip_id}"
        streamer = AgentStreamer(pubsub_channel)
        
        user_msg_dict = {
            "id": str(uuid.uuid4()),
            "role": "user",
            "content": message
        }
        fallback_msg = None
        
        try:
            # Execute the core business logic (LangGraph)
            return await func(trip_id, message, user_id, correlation_id, itinerary_draft, streamer, *args, **kwargs)
            
        except (LLMCoreError, GraphStateError) as e:
            log.critical(f"Fatal Agent Error Caught by Boundary: {e}", exc_info=True)
            fallback_msg = await _execute_fallback_llm(message, trip_id, user_id, correlation_id, streamer)
            
        except Exception as e:
            log.critical(f"Unknown Fatal System Error Caught by Boundary: {e}", exc_info=True)
            fallback_msg = await _execute_fallback_llm(message, trip_id, user_id, correlation_id, streamer)
            
        finally:
            # --- ATOMIC UI TRANSACTION ---
            # Unbreakable guarantee: If the fallback generated a message, we sync it to the UI database.
            # If the graph succeeded, the inner function already updated the DB, or we can update it here.
            # Wait, if the inner function succeeded, we should extract the final message from the checkpoint.
            
            try:
                # 1. Grab the AI response (either Fallback or from Checkpoint)
                ai_msg_dict = None
                if fallback_msg:
                    ai_msg_dict = {
                        "id": str(uuid.uuid4()),
                        "role": "agent",
                        "content": str(fallback_msg)
                    }
                else:
                    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
                    from src.core.database import DATABASE_URL
                    conn_string = DATABASE_URL.replace("+asyncpg", "")
                    async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
                        config = {"configurable": {"thread_id": trip_id}}
                        final_state = await checkpointer.aget(config)
                        if final_state and "channel_values" in final_state and "messages" in final_state["channel_values"]:
                            last_message = final_state["channel_values"]["messages"][-1]
                            ai_msg_dict = {
                                "id": getattr(last_message, "id", str(uuid.uuid4())),
                                "role": "agent",
                                "content": str(last_message.content)
                            }
                
                if ai_msg_dict:
                    clean_delta = [user_msg_dict, ai_msg_dict]
                    await _atomic_db_append(trip_id, user_id, clean_delta)
                    log.info("Transaction safely committed to UI Database.")
                
            except Exception as db_err:
                log.error(f"FATAL: Failed to sync ChatHistory transaction: {db_err}", exc_info=True)
                
            # Unlock the UI
            await streamer.finish()
            
            # Clean up Redis connection explicitly
            from src.core.telemetry import close_telemetry_redis
            await close_telemetry_redis()
            
    return wrapper

async def _execute_fallback_llm(user_message: str, trip_id: str, user_id: str, correlation_id: str, streamer: AgentStreamer) -> str:
    """Executes the emergency raw LLM fallback."""
    try:
        from src.core.config import get_llm
        llm = get_llm(temperature=0.4)
        config = {
            "configurable": {"thread_id": trip_id, "user_id": user_id},
            "metadata": {"correlation_id": correlation_id}
        }
        fallback_msg = await llm.ainvoke([
            {"role": "system", "content": "You are a Travel Assistant. The AI system just crashed due to a critical error. Apologize politely to the user based on their last request."},
            {"role": "user", "content": user_message}
        ], config=config)
        
        await streamer.stream_token(str(fallback_msg.content))
        return str(fallback_msg.content)
    except Exception as e:
        logger.error(f"Fallback LLM failed: {e}", exc_info=True)
        hardcoded_msg = "I'm so sorry, but I encountered a critical system error while planning this. Please try again."
        await streamer.stream_token(hardcoded_msg)
        return hardcoded_msg

async def _atomic_db_append(trip_id: str, user_id: str, delta_messages: list):
    """Executes the zero-read atomic JSONB append to ChatHistory."""
    trip_uuid = uuid.UUID(trip_id)
    user_uuid = uuid.UUID(user_id)
    
    async with AsyncSessionLocal() as session:
        update_query = text(
            "UPDATE chat_history SET messages = messages || CAST(:new_msgs AS jsonb), updated_at = NOW() "
            "WHERE trip_id = :trip_id RETURNING id"
        )
        result = await session.execute(update_query, {"new_msgs": json.dumps(delta_messages), "trip_id": trip_uuid})
        
        if not result.scalars().first():
            insert_query = text(
                "INSERT INTO chat_history (id, user_id, trip_id, messages, created_at, updated_at) "
                "VALUES (:id, :user_id, :trip_id, CAST(:msgs AS jsonb), NOW(), NOW())"
            )
            await session.execute(insert_query, {
                "id": uuid.uuid4(), 
                "user_id": user_uuid, 
                "trip_id": trip_uuid, 
                "msgs": json.dumps(delta_messages)
            })
        await session.commit()
