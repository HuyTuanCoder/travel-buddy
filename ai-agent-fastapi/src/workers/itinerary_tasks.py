import os
import json
import asyncio
import structlog
import redis.asyncio as redis
from celery import shared_task
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

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
    fallback_msg = None
    
    try:
        await publish_thought(pubsub_channel, "AI is processing your request...")

        conn_string = DATABASE_URL.replace("+asyncpg", "")
        async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
            app_graph = build_graph(checkpointer)
            
            inputs = {
                "messages": [("user", message)]
            }
            if itinerary_draft is not None:
                # The frontend sends a bundle: { "itinerary": {...}, "metadata": {...} }
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
                    "langfuse_tags": ["chat", "v2"],
                    "correlation_id": correlation_id,
                }
            }

            try:
                # Run graph with fake streaming
                log.info("Invoking LangGraph with streaming")
                text_buffer = ""
            
                async for event in app_graph.astream_events(inputs, config=config, version="v2"):
                    kind = event["event"]
                    node_name = event["metadata"].get("langgraph_node")
                
                    if kind == "on_chat_model_stream":
                        content = event["data"]["chunk"].content
                        if content and isinstance(content, str):
                            if node_name == "speaker":
                                # Stream instantly in real-time to chat bubble!
                                await publish_token(pubsub_channel, content)
                            elif node_name == "executor":
                                # Buffer internal reasoning to send as a complete thought block
                                text_buffer += content
                            
                    elif kind == "on_chat_model_end":
                        if node_name == "executor":
                            if text_buffer.strip():
                                await publish_thought(pubsub_channel, text_buffer.strip())
                                text_buffer = ""
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
                
                log.info("Chat task completed successfully")
                
            except Exception as e:
                log.error("Chat task failed during graph execution", exc_info=True)
                
                # Graceful Error Handoff: Output the raw error to the AI thought frontend
                await publish_event(pubsub_channel, "thought", f"\n> [SYSTEM ERROR]: {str(e)}\n> Handing off to Speaker for graceful recovery...\n")
                
                try:
                    from src.agent.nodes.speaker import call_speaker
                    
                    # Grab the latest state from the checkpoint
                    final_state = await app_graph.aget_state(config)
                    current_state = final_state.values if final_state.values else {}
                    
                    # Inject the error so the speaker knows what happened
                    current_summary = current_state.get("running_summary", "")
                    current_state["running_summary"] = current_summary + f"\n[CRITICAL SYSTEM ERROR OCCURRED]: {str(e)}. The background task failed. You must apologize to the user and explain that you could not complete their last request due to a technical error."
                    
                    # Call the speaker node directly to synthesize the final response
                    speaker_result = await call_speaker(current_state, config)
                    
                    # Stream the speaker's response to the frontend chat bubble
                    fallback_response = speaker_result["messages"][0]
                    words = str(fallback_response.content).split(" ")
                    for i, word in enumerate(words):
                        chunk = word + " " if i < len(words) - 1 else word
                        await publish_token(pubsub_channel, chunk)
                        await asyncio.sleep(0.02)
                        
                    # Save this fallback response so it gets logged to ChatHistory DB below
                    fallback_msg = fallback_response
                        
                except Exception as fallback_e:
                    log.error(f"Speaker fallback failed: {fallback_e}")
                    await publish_event(pubsub_channel, "error", "I'm sorry, I encountered a critical internal system error and could not complete your request. Please try again.")
            finally:
                # --- CHAT HISTORY DB MIGRATION ---
                # Guarantee that whatever is in the checkpointer gets flushed to ChatHistory
                import uuid
                import json
                
                # 1. Isolate the User's input message
                user_msg_dict = {
                    "id": str(uuid.uuid4()),
                    "role": "user",
                    "content": message
                }
                
                # 2. Isolate the Speaker's pristine final response from the LangGraph state
                if fallback_msg:
                    speaker_msg = fallback_msg
                else:
                    final_state = await app_graph.aget_state(config)
                    final_messages = final_state.values.get("messages", []) if final_state.values else []
                    speaker_msg = final_messages[-1] if final_messages else None
                
                clean_delta = [user_msg_dict]
                
                # Verify that the final node actually emitted an AI message (not an internal tool call)
                if speaker_msg and getattr(speaker_msg, "type", "") == "ai":
                    clean_delta.append({
                        "id": str(getattr(speaker_msg, "id", uuid.uuid4())),
                        "role": "agent",
                        "content": str(getattr(speaker_msg, "content", ""))
                    })
                            
                # 3. ZERO-READ UPSERT into ChatHistory Postgres table
                from src.core.database import AsyncSessionLocal
                from sqlalchemy import text
                
                trip_uuid = uuid.UUID(trip_id)
                user_uuid = uuid.UUID(user_id)
                
                async with AsyncSessionLocal() as session:
                    # Try to atomically append to the JSONB array without reading it
                    update_query = text(
                        "UPDATE chat_history SET messages = messages || CAST(:new_msgs AS jsonb) "
                        "WHERE trip_id = :trip_id RETURNING id"
                    )
                    result = await session.execute(
                        update_query,
                        {"new_msgs": json.dumps(clean_delta), "trip_id": trip_uuid}
                    )
                    
                    if not result.scalars().first():
                        # If no row was updated, the trip doesn't exist in ChatHistory yet, so insert it
                        insert_query = text(
                            "INSERT INTO chat_history (id, user_id, trip_id, messages) "
                            "VALUES (:id, :user_id, :trip_id, CAST(:msgs AS jsonb))"
                        )
                        await session.execute(
                            insert_query,
                            {
                                "id": uuid.uuid4(), 
                                "user_id": user_uuid, 
                                "trip_id": trip_uuid, 
                                "msgs": json.dumps(clean_delta)
                            }
                        )
                    await session.commit()
                # ---------------------------------
                
                await publish_event(pubsub_channel, "done", "")
                
    except Exception as e:
        log.error("Fatal graph error intercepted", exc_info=True)
        await publish_thought(pubsub_channel, "Encountered a system error. Recovering...")
        
        try:
            from src.core.config import get_llm
            from langchain_core.messages import AIMessage
            llm = get_llm(temperature=0.4)
            fallback_msg = await llm.ainvoke([
                {"role": "system", "content": "You are a Travel Assistant. The system just crashed while trying to fulfill the user's request. Apologize politely and tell them to try again."},
                {"role": "user", "content": message}
            ], config=config)
            
            # Stream the fallback message cleanly
            await publish_event(pubsub_channel, "token", fallback_msg.content)
            await publish_event(pubsub_channel, "done", "")
        except Exception as inner_e:
            log.error("Fallback LLM failed", exc_info=True)
            # Hardcoded failsafe if even the LLM crashes
            from langchain_core.messages import AIMessage
            fallback_msg = AIMessage(content="I'm so sorry, but I encountered a critical system error while planning this. Please try again.")
            await publish_event(pubsub_channel, "token", fallback_msg.content)
            await publish_event(pubsub_channel, "done", "")

# ---------------------------------------------------------
# Celery Sync Wrappers (The entrypoints for RabbitMQ)
# ---------------------------------------------------------
@shared_task(name="process_chat_message")
def process_chat_message(trip_id: str, message: str, user_id: str, correlation_id: str, itinerary_draft: dict = None):
    # This runs inside the Celery worker process
    asyncio.run(_run_chat(trip_id, message, user_id, correlation_id, itinerary_draft))
