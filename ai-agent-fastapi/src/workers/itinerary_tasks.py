import os
import json
import uuid
import asyncio
from sqlalchemy import text
from src.core.database import AsyncSessionLocal
import structlog
import redis.asyncio as redis
from celery import shared_task
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.agent.graph import build_graph
from src.core.database import DATABASE_URL
from src.core.config import settings
from src.core.telemetry import publish_thought, publish_token, publish_event
from src.core.streamer import AgentStreamer
from src.core.error_handlers import celery_agent_boundary
from src.exceptions.agent import LLMCoreError, GraphStateError

REDIS_URL = settings.REDIS_URL
logger = structlog.get_logger(__name__)


# ---------------------------------------------------------
# Core Async Handlers that run LangGraph
# ---------------------------------------------------------
@celery_agent_boundary
async def _run_chat(trip_id: str, message: str, user_id: str, correlation_id: str, itinerary_draft: dict, streamer: AgentStreamer):
    log = logger.bind(thread_id=trip_id, user_id=user_id, correlation_id=correlation_id)
    log.info("Starting AI chat task")
    
    await streamer.stream_thought("AI is processing your request...")

    conn_string = DATABASE_URL.replace("+asyncpg", "")
    async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
        app_graph = build_graph(checkpointer)
        
        inputs = {
            "messages": [("user", message)]
        }
        if itinerary_draft is not None:
            if isinstance(itinerary_draft, dict) and "itinerary" in itinerary_draft:
                inputs["itinerary_draft"] = itinerary_draft.get("itinerary")
                inputs["user_modifications"] = itinerary_draft.get("metadata", {})
            else:
                inputs["itinerary_draft"] = itinerary_draft
        
        config = {
            "configurable": {"thread_id": trip_id, "user_id": user_id},
            "metadata": {
                "langfuse_user_id": user_id,
                "langfuse_session_id": trip_id,
                "correlation_id": correlation_id,
            }
        }

        from src.core.langfuse_compat import CallbackHandler
        langfuse_handler = CallbackHandler()
        config["callbacks"] = [langfuse_handler]
        
        # --- Time Travel Rollback for Crash Recovery ---
        import uuid
        current_state = await app_graph.aget_state(config)
        if current_state.next:
            log.warning(f"Thread {trip_id} is in a poisoned state (crashed at {current_state.next}). Initiating Time Travel Rollback.")
            healthy_config = None
            async for past_state in app_graph.aget_state_history(config):
                if not past_state.next:
                    healthy_config = past_state.config
                    break
            
            if healthy_config:
                config = healthy_config
                log.info(f"Successfully rolled back thread {trip_id} to last healthy checkpoint.")
            else:
                log.error("No healthy checkpoint found. Thread is unrecoverable. Resetting thread.")
                config["configurable"]["thread_id"] = f"{trip_id}-reset-{uuid.uuid4().hex[:8]}"
        # -----------------------------------------------

        log.info("Invoking LangGraph with streaming")
        text_buffer = ""
    
        async for event in app_graph.astream_events(inputs, config=config, version="v2"):
            kind = event["event"]
            node_name = event["metadata"].get("langgraph_node")
        
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content and isinstance(content, str):
                    if node_name in ["speaker", "early_exit"]:
                        await streamer.stream_token(content)
                    elif node_name == "executor":
                        text_buffer += content
                    
            elif kind == "on_chat_model_end":
                if node_name == "executor":
                    if text_buffer.strip():
                        await streamer.stream_thought(text_buffer.strip())
                        text_buffer = ""
            elif kind == "on_tool_start":
                await streamer.stream_tool_start(event['name'])
            elif kind == "on_tool_end":
                tool_output = event["data"].get("output")
                if tool_output:
                    content = str(getattr(tool_output, "content", tool_output)).strip()
                    status = "FAILED" if not content or content == "[]" or content.startswith("Error:") else "SUCCESS"
                    
                    if status == "SUCCESS" and event["name"].startswith("draft_"):
                        import json
                        try:
                            action_json = json.loads(content)
                            print(f"DRAFT UPDATE SENT: {action_json}")
                            await streamer.stream_draft_update(action_json)
                        except Exception as e:
                            print(f"JSON ERROR: {e}, content: {content}")

                    await streamer.stream_tool_result(event['name'], content, status)

        # Check if paused before a tool execution
        state = await app_graph.aget_state(config)
        
        if state.next and "tools" in state.next:
            import json
            last_msg = state.values["messages"][-1]
            await publish_event(streamer.pubsub_channel, "tool_call", json.dumps([{
                "name": tool_call.get("name"),
                "args": tool_call.get("args")
            } for tool_call in getattr(last_msg, "tool_calls", [])]))
        
        log.info("Chat task completed successfully")
        
        # Ensure Langfuse telemetry background threads finish uploading using the CallbackHandler
        if hasattr(langfuse_handler, "flush"):
            langfuse_handler.flush()
                


# ---------------------------------------------------------
# Celery Sync Wrappers (The entrypoints for RabbitMQ)
# ---------------------------------------------------------
@shared_task(name="process_chat_message")
def process_chat_message(trip_id: str, message: str, user_id: str, correlation_id: str, itinerary_draft: dict = None):
    # This runs inside the Celery worker process
    asyncio.run(_run_chat(trip_id, message, user_id, correlation_id, itinerary_draft))
