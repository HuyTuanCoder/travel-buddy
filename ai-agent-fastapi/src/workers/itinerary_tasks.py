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
from src.core.telemetry import publish_thought, publish_token, publish_event

REDIS_URL = settings.REDIS_URL
logger = structlog.get_logger(__name__)

# ---------------------------------------------------------
# Core Async Handlers that run LangGraph
# ---------------------------------------------------------
async def _run_chat(trip_id: str, message: str, user_id: str, correlation_id: str, itinerary_draft: dict = None):
    log = logger.bind(thread_id=trip_id, user_id=user_id, correlation_id=correlation_id)
    log.info("Starting AI chat task")
    
    pubsub_channel = f"stream:{trip_id}"
    
    try:
        await publish_thought(pubsub_channel, "AI is processing your request...")

        conn_string = DATABASE_URL.replace("+asyncpg", "")
        async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
            app_graph = build_graph(checkpointer)
            
            inputs = {
                "messages": [("user", message)]
            }
            if itinerary_draft is not None:
                inputs["itinerary_draft"] = itinerary_draft
            
            # Setup Langfuse tracing with full metadata
            langfuse_handler = CallbackHandler()
            
            config = {
                "configurable": {"thread_id": trip_id, "user_id": user_id},
                "callbacks": [langfuse_handler],
                "metadata": {
                    "langfuse_user_id": user_id,
                    "langfuse_session_id": trip_id,
                    "langfuse_tags": ["chat", "v2"],
                    "correlation_id": correlation_id,
                }
            }

            # Run graph with true token-by-token streaming
            log.info("Invoking LangGraph with streaming")
            current_run_id = None
            async for event in app_graph.astream_events(inputs, config=config, version="v2"):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    run_id = event["run_id"]
                    if current_run_id != run_id:
                        current_run_id = run_id
                        await publish_event(pubsub_channel, "new_run", "")

                    content = event["data"]["chunk"].content
                    if content and isinstance(content, str):
                        await publish_token(pubsub_channel, content)
                elif kind == "on_tool_start":
                    await publish_thought(pubsub_channel, f"\n\n> Executing action: {event['name']}...\n")
                elif kind == "on_tool_end":
                    tool_output = event["data"].get("output")
                    if tool_output:
                        content = str(getattr(tool_output, "content", tool_output)).strip()
                        
                        if not content or content == "[]" or content.startswith("Error:"):
                            status = "FAILED"
                        else:
                            status = "SUCCESS"
                            
                            # Instantly broadcast draft actions to prevent duplicates and sync UI
                            tool_name = event["name"]
                            if tool_name in ["draft_add_stop", "draft_remove_stop", "draft_update_stop", "draft_move_stop_between_days"]:
                                try:
                                    # The tool returns JSON string of the draft action
                                    action_json = json.loads(content)
                                    # Wrap it in an array so the frontend processes it
                                    await publish_event(pubsub_channel, "draft_update", json.dumps([action_json]))
                                except Exception as e:
                                    logger.error(f"Failed to parse draft tool output: {e}")

                        display_content = content[:97] + "..." if len(content) > 100 else content
                        await publish_event(pubsub_channel, "thought", f"> Action {event['name']} {status}: {display_content}\n")
            
            # Check if paused before a tool execution
            state = await app_graph.aget_state(config)
            
            if state.next and "tools" in state.next:
                last_msg = state.values["messages"][-1]
                await publish_event(pubsub_channel, "tool_call", json.dumps([{
                    "name": tool_call.get("name"),
                    "args": tool_call.get("args")
                } for tool_call in getattr(last_msg, "tool_calls", [])]))
            else:
                # Execution completely finished (e.g. Critic approved)
                await publish_event(pubsub_channel, "done", "")
            
            log.info("Chat task completed successfully")
    except Exception as e:
        log.error("Chat task failed", exc_info=True)
        await publish_event(pubsub_channel, "error", f"Task Failed: {str(e)}")
        await publish_event(pubsub_channel, "done", "")
    finally:
        if 'langfuse_handler' in locals():
            langfuse_handler.flush()

async def _run_approve(trip_id: str, user_id: str, correlation_id: str):
    log = logger.bind(thread_id=trip_id, user_id=user_id, correlation_id=correlation_id)
    log.info("Starting tool approval task")
    
    pubsub_channel = f"stream:{trip_id}"
    
    try:
        await publish_thought(pubsub_channel, "Executing approved changes via Java gRPC...")

        conn_string = DATABASE_URL.replace("+asyncpg", "")
        async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
            app_graph = build_graph(checkpointer)
            
            # Setup Langfuse tracing with full metadata
            langfuse_handler = CallbackHandler()
            
            config = {
                "configurable": {"thread_id": trip_id, "user_id": user_id},
                "callbacks": [langfuse_handler],
                "metadata": {
                    "langfuse_user_id": user_id,
                    "langfuse_session_id": trip_id,
                    "langfuse_tags": ["approve", "v2"],
                    "correlation_id": correlation_id,
                }
            }
            
            state = await app_graph.aget_state(config)
            if not state.next or "commit_tools" not in state.next:
                log.warning("No tool call pending approval")
                await publish_event(pubsub_channel, "error", "No tool call pending approval.")
                return

            # Resume the graph by passing None as input
            log.info("Resuming LangGraph execution with streaming")
            current_run_id = None
            async for event in app_graph.astream_events(None, config=config, version="v2"):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    run_id = event["run_id"]
                    if current_run_id != run_id:
                        current_run_id = run_id
                        await publish_event(pubsub_channel, "new_run", "")
                    content = event["data"]["chunk"].content
                    if content and isinstance(content, str):
                        await publish_token(pubsub_channel, content)
                elif kind == "on_tool_start":
                    await publish_thought(pubsub_channel, f"\n\n> System executing action: {event['name']}...\n")
                elif kind == "on_tool_end":
                    tool_output = event["data"].get("output")
                    if tool_output:
                        content = str(getattr(tool_output, "content", tool_output)).strip()
                        
                        if not content or content == "[]" or content.startswith("Error:"):
                            status = "FAILED"
                        else:
                            status = "SUCCESS"
                            
                        display_content = content[:97] + "..." if len(content) > 100 else content
                        await publish_thought(pubsub_channel, f"> Action {event['name']} {status}: {display_content}\n")

            # Check if paused again (e.g. multi-step tool calls)
            new_state = await app_graph.aget_state(config)
            
            # Broadcast the latest draft to the frontend so the UI stays synced
            current_draft = new_state.values.get("itinerary_draft", [])
            await publish_event(pubsub_channel, "draft_update", json.dumps(current_draft))
            
            if new_state.next and "commit_tools" in new_state.next:
                last_msg = new_state.values["messages"][-1]
                await publish_event(pubsub_channel, "tool_call", json.dumps([{
                    "name": tool_call.get("name"),
                    "args": tool_call.get("args")
                } for tool_call in getattr(last_msg, "tool_calls", [])]))
            else:
                # Execution completely finished (e.g. Critic approved)
                await publish_event(pubsub_channel, "done", "")
            
            log.info("Tool approval task completed successfully")
    except Exception as e:
        log.error("Tool approval task failed", exc_info=True)
        await publish_event(pubsub_channel, "error", f"Task Failed: {str(e)}")
        await publish_event(pubsub_channel, "done", "")
    finally:
        if 'langfuse_handler' in locals():
            langfuse_handler.flush()

# ---------------------------------------------------------
# Celery Sync Wrappers (The entrypoints for RabbitMQ)
# ---------------------------------------------------------
@shared_task(name="process_chat_message")
def process_chat_message(trip_id: str, message: str, user_id: str, correlation_id: str, itinerary_draft: dict = None):
    # This runs inside the Celery worker process
    asyncio.run(_run_chat(trip_id, message, user_id, correlation_id, itinerary_draft))

@shared_task(name="approve_tool_call")
def approve_tool_call(trip_id: str, user_id: str, correlation_id: str):
    """
    Resumes a paused execution from the DB.
    """
    asyncio.run(_run_approve(trip_id, user_id, correlation_id))
