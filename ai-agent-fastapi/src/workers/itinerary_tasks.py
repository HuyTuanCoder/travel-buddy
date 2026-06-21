import os
import json
import asyncio
import structlog
import redis.asyncio as redis
from celery import shared_task
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langfuse.callback import CallbackHandler

from src.agent.graph import build_graph
from src.core.database import DATABASE_URL
from src.core.config import settings

REDIS_URL = settings.REDIS_URL
logger = structlog.get_logger(__name__)

# ---------------------------------------------------------
# Core Async Handlers that run LangGraph
# ---------------------------------------------------------
async def _run_chat(trip_id: str, message: str, user_id: str, correlation_id: str):
    log = logger.bind(thread_id=trip_id, user_id=user_id, correlation_id=correlation_id)
    log.info("Starting AI chat task")
    
    redis_client = redis.from_url(REDIS_URL)
    pubsub_channel = f"stream:{trip_id}"
    
    try:
        # Example data shape: {"event": "status", "data": "Processing..."}
        await redis_client.publish(pubsub_channel, json.dumps({
            "event": "status",
            "data": "AI is processing your request..."
        }))

        async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
            app_graph = build_graph(checkpointer)
            inputs = {"messages": [("user", message)]}
            
            # Setup Langfuse tracing
            langfuse_handler = CallbackHandler()
            
            config = {
                "configurable": {"thread_id": trip_id},
                "callbacks": [langfuse_handler]
            }

            # Run graph
            log.info("Invoking LangGraph")
            await app_graph.ainvoke(inputs, config=config)
            
            # Check if paused before a tool execution
            state = await app_graph.aget_state(config)
            
            if state.next and "tools" in state.next:
                last_msg = state.values["messages"][-1]
                # Convert tool calls to dict format for the frontend
                await redis_client.publish(pubsub_channel, json.dumps({
                    "event": "requires_approval",
                    "data": last_msg.tool_calls
                }))
            else:
                ai_response = state.values["messages"][-1].content
                await redis_client.publish(pubsub_channel, json.dumps({
                    "event": "completed",
                    "data": ai_response
                }))
                log.info("Chat task completed successfully")
    except Exception as e:
        log.error("Chat task failed", exc_info=True)
        await redis_client.publish(pubsub_channel, json.dumps({
            "event": "error",
            "data": f"Task Failed: {str(e)}"
        }))
    finally:
        await redis_client.close()

async def _run_approve(trip_id: str, user_id: str, correlation_id: str):
    log = logger.bind(thread_id=trip_id, user_id=user_id, correlation_id=correlation_id)
    log.info("Starting tool approval task")
    
    redis_client = redis.from_url(REDIS_URL)
    pubsub_channel = f"stream:{trip_id}"
    
    try:
        await redis_client.publish(pubsub_channel, json.dumps({
            "event": "status",
            "data": "Executing approved changes via Java gRPC..."
        }))

        async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
            app_graph = build_graph(checkpointer)
            
            # Setup Langfuse tracing
            langfuse_handler = CallbackHandler()
            
            config = {
                "configurable": {"thread_id": trip_id},
                "callbacks": [langfuse_handler]
            }
            
            state = await app_graph.aget_state(config)
            if not state.next or "tools" not in state.next:
                log.warning("No tool call pending approval")
                await redis_client.publish(pubsub_channel, json.dumps({
                    "event": "error",
                    "data": "No tool call pending approval."
                }))
                return

            # Resume the graph by passing None as input
            log.info("Resuming LangGraph execution")
            await app_graph.ainvoke(None, config=config)
            
            # Check state again to see if it finished or hit another tool interrupt
            new_state = await app_graph.aget_state(config)
            
            if new_state.next and "tools" in new_state.next:
                last_msg = new_state.values["messages"][-1]
                await redis_client.publish(pubsub_channel, json.dumps({
                    "event": "requires_approval",
                    "data": last_msg.tool_calls
                }))
            else:
                ai_response = new_state.values["messages"][-1].content
                await redis_client.publish(pubsub_channel, json.dumps({
                    "event": "completed",
                    "data": ai_response
                }))
                log.info("Tool approval task completed successfully")
    except Exception as e:
        log.error("Tool approval task failed", exc_info=True)
        await redis_client.publish(pubsub_channel, json.dumps({
            "event": "error",
            "data": f"Task Failed: {str(e)}"
        }))
    finally:
        await redis_client.close()

# ---------------------------------------------------------
# Celery Sync Wrappers (The entrypoints for RabbitMQ)
# ---------------------------------------------------------
@shared_task(name="process_chat_message")
def process_chat_message(trip_id: str, message: str, user_id: str, correlation_id: str):
    """
    Pulled from RabbitMQ by the Celery worker pod.
    Runs the async logic in the synchronous Celery thread.
    """
    asyncio.run(_run_chat(trip_id, message, user_id, correlation_id))

@shared_task(name="approve_tool_call")
def approve_tool_call(trip_id: str, user_id: str, correlation_id: str):
    """
    Resumes a paused execution from the DB.
    """
    asyncio.run(_run_approve(trip_id, user_id, correlation_id))
