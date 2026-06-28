from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import RemoveMessage
import logging

from src.schemas.agent import AgentState
from src.agent.nodes.llm_node import call_executor
from src.agent.nodes.speaker import call_speaker
from src.agent.nodes.validator import validate_tool_call
from src.core.error_handlers import node_error_boundary
from src.agent.nodes.rag_injector import inject_memories
from src.agent.nodes.planner import plan_itinerary
from src.agent.nodes.critic import evaluate_itinerary
from src.agent.nodes.reflection import reflection_node
from src.agent.nodes.router import semantic_router
from src.agent.nodes.early_exit import early_exit_node

from src.agent.tools.discovery import search_web, read_webpage, find_and_register_place
from src.agent.tools.draft import (
    draft_add_stop, draft_remove_stop, draft_update_stop, draft_move_stop, 
    draft_add_day, draft_remove_day, draft_restore_day, draft_restore_stop, draft_swap_days
)
from src.workers.memory_tasks import process_evicted_memory
from src.core.telemetry import publish_thought
from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)

# custom router to check if llm try to call a tool
def route_from_executor(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "validator" # Go to Validator for Schema Check
    return "critic" # No tools, go to Gate 3: Critic Node for draft evaluation

# custom router to check if Pydantic reject the json
def router_from_validator(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # We always route to auto_tools, even if there are validation errors,
        # so that the valid tool calls (which don't have ToolMessages yet) can be executed.
        return "auto_tools"
    return "executor"

# custom router to check if Critic approved or rejected
def route_from_critic(state: AgentState):
    if state.get("critic_feedback"):
        # Critic rejected. Bounce back to agent to fix.
        return "executor"
    return "speaker" # Approved final text. Go to Speaker to synthesize response.

# custom router to check if auto_tools returned an empty/error result
def route_after_auto_tools(state: AgentState):
    messages = state.get("messages", [])
    if not messages:
        return "executor"
    
    last_message = messages[-1]
    if last_message.type == "tool":
        content = str(last_message.content).strip()
        # Trigger reflection if the tool returned an empty array, empty string, or an explicit Error
        if not content or content == "[]" or content.startswith("Error:"):
            return "reflection"
            
    return "executor"

@node_error_boundary
async def memory_manager(state: AgentState, config: RunnableConfig):
    """
    Tier 1 Context Window Manager.
    Evicts oldest messages based on Token Count to prevent parallel tool calls from wiping history.
    """
    messages = state.get("messages", [])
    
    # 1 token ~= 4 chars roughly
    total_chars = sum(len(str(msg.content)) for msg in messages if msg.content)
    estimated_tokens = total_chars // 4
    
    if estimated_tokens <= 4000:
        return {"messages": []}
        
    logger.info(f"Context window exceeded 4000 tokens (est: {estimated_tokens}). Sweeping older messages.")
    
    # Keep the system prompt (index 0) and the most recent ~2000 tokens
    start_idx = 1 if messages[0].type == "system" else 0
    
    # Find how many messages to drop from the front to bring tokens down
    chars_to_drop = (estimated_tokens - 2000) * 4
    dropped_chars = 0
    num_to_drop = 0
    
    for i in range(start_idx, len(messages)):
        if dropped_chars >= chars_to_drop:
            break
        dropped_chars += len(str(messages[i].content)) if messages[i].content else 0
        num_to_drop += 1
        
    messages_to_drop = messages[start_idx : start_idx + num_to_drop]
    drop_commands = [RemoveMessage(id=msg.id) for msg in messages_to_drop if msg.id]
    
    # --- Tier 0.5: Narrative Summarizer ---
    existing_summary = state.get("running_summary", "")
    from src.agent.utils import get_conversational_transcript
    from src.core.config import get_llm
    
    transcript_of_dropped = get_conversational_transcript(messages_to_drop, turns=10)
    new_summary = existing_summary
    
    if transcript_of_dropped:
        logger.info("Generating narrative summary of evicted messages...")
        llm = get_llm(temperature=0)
        prompt = f"""
You are the Narrative Memory Engine for an AI Travel Agent.
You are receiving a batch of older messages that are about to be deleted from the context window.
You must update the existing RUNNING_SUMMARY with the new events.

CRITICAL INSTRUCTIONS:
1. NEVER write vague summaries like "The agent discussed museums."
2. You MUST preserve hard data discovered by the agent. If the agent used a tool to find that the Louvre opens at 9 AM and costs 22 Euros, your summary MUST include "Louvre: 9 AM, 22 Euros".
3. You MUST preserve user decisions. If the user rejected a hotel, state exactly why (e.g., "User rejected Hotel X because it lacks a gym").

EXISTING SUMMARY:
{existing_summary}

NEW MESSAGES TO INCORPORATE:
{transcript_of_dropped}

1-SHOT EXAMPLE OF A PERFECT SUMMARY UPDATE:
Existing: The user is planning a trip to Tokyo.
New Messages:
USER: I want to visit a museum tomorrow.
SYSTEM: [Tool 'search_web' completed. Result: The Mori Art Museum opens at 10 AM and costs 2000 Yen.]
AGENT: The Mori Art Museum is a great choice! It opens at 10 AM and tickets are 2000 Yen.
Output: The user is planning a trip to Tokyo and wants to visit a museum. The agent found the Mori Art Museum, which opens at 10 AM (2000 Yen).

Return ONLY the updated paragraph.
"""
        new_summary = llm.invoke(prompt).content
            
    # Send texts to Celery for Tier 2 Delta Extraction
    texts_to_extract = [msg.content for msg in messages_to_drop if isinstance(msg.content, str)]
    
    user_id = config.get("configurable", {}).get("user_id", "default_user")
    trip_id = config.get("configurable", {}).get("thread_id", "default_trip")
    
    if texts_to_extract:
        if trip_id != "default_trip":
            await publish_thought(f"stream:{trip_id}", f"\n\n> Archiving {len(texts_to_extract)} old messages to Long-Term Memory...\n")
                
        # Fire and forget async Celery task
        process_evicted_memory.delay(texts_to_extract, user_id, trip_id)
        
    return {"messages": drop_commands, "running_summary": new_summary}

def build_graph(checkpointer: AsyncPostgresSaver = None):
    # initial graph with specific state (memory)
    builder = StateGraph(AgentState)

    # add our nodes
    builder.add_node("semantic_router", semantic_router)
    builder.add_node("early_exit", early_exit_node)
    builder.add_node("rag_injector", inject_memories)
    builder.add_node("planner", plan_itinerary)
    builder.add_node("executor", call_executor)
    builder.add_node("speaker", call_speaker)
    builder.add_node("auto_tools", ToolNode([
        search_web, read_webpage, find_and_register_place,
        draft_add_stop, draft_remove_stop, draft_update_stop, draft_move_stop, 
        draft_add_day, draft_remove_day, draft_restore_day, draft_restore_stop, draft_swap_days
    ]))
    builder.add_node("validator", validate_tool_call)
    builder.add_node("critic", evaluate_itinerary)
    builder.add_node("reflection", reflection_node)
    builder.add_node("memory_manager", memory_manager)

    # draw the entry edge -> goes to Router first
    builder.add_edge(START, "semantic_router")
    
    # conditional edge from router
    def route_from_start(state: AgentState):
        intent = state.get("intent", "TRAVEL_PLANNING")
        if intent in ["TRAVEL_PLANNING", "TRAVEL_PLANNING_RESET"]:
            return "rag_injector"
        return "early_exit"
        
    builder.add_conditional_edges("semantic_router", route_from_start)
    builder.add_edge("early_exit", END)
    
    # RAG -> Planner -> Executor
    builder.add_edge("rag_injector", "planner")
    builder.add_edge("planner", "executor")

    # conditional edge from executor
    builder.add_conditional_edges("executor", route_from_executor)
    
    # conditional edge from validator
    builder.add_conditional_edges("validator", router_from_validator)

    # conditional edge from critic
    builder.add_conditional_edges("critic", route_from_critic)
    
    # route from auto_tools conditionally to reflection on failure
    builder.add_conditional_edges("auto_tools", route_after_auto_tools)
    builder.add_edge("reflection", "executor")
    
    # Speaker to memory manager
    builder.add_edge("speaker", "memory_manager")
    
    # memory manager always ends
    builder.add_edge("memory_manager", END)

    return builder.compile(checkpointer=checkpointer)
