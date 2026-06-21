from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import RemoveMessage
import logging

from src.schemas.agent import AgentState
from src.agent.nodes.llm_node import call_gemini
from src.agent.nodes.validator import validate_tool_call
from src.agent.nodes.rag_injector import inject_memories
from src.agent.nodes.planner import plan_itinerary
from src.agent.nodes.critic import evaluate_itinerary
from src.agent.tools.itinerary import add_stop, remove_stop, update_stop, move_stop_between_days
from src.workers.memory_tasks import process_evicted_memory

logger = logging.getLogger(__name__)

# custom router to check if llm try to call a tool
def route_from_agent(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "validator" # Go to Validator for Schema Check
    return "critic" # No tools, go to Gate 3: Critic Node for final text check

# custom router to check if Pydantic reject the json
def router_from_validator(state: AgentState):
    if state.get("validation_error"):
        return "agent" # bounce back to llm
    return "critic" # SCHEMA IS VALID! Send to Critic for Logic Check!

# custom router to check if Critic approved or rejected
def route_from_critic(state: AgentState):
    if state.get("critic_feedback"):
        # Critic rejected (either bad JSON logic or bad final text). Bounce back to agent to fix.
        return "agent"
        
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools" # Critic approved the tool call! Go execute it!
        
    return "memory_manager" # Approved final text. Safe to process memory and end.

def memory_manager(state: AgentState, config: dict):
    """
    Tier 1 Context Window Manager.
    If the context window grows beyond 10 messages, we evict the oldest messages
    (excluding the System message) and send them to the Tier 2 Celery task for extraction.
    """
    messages = state.get("messages", [])
    
    # We want to keep at most 10 messages (plus system prompt if any)
    if len(messages) <= 10:
        return {}
        
    logger.info(f"Context window exceeded 10 messages. Evicting {len(messages) - 10} oldest messages.")
    
    # Identify messages to drop (skip index 0 if it's a SystemMessage)
    start_idx = 1 if messages[0].type == "system" else 0
    num_to_drop = len(messages) - 10
    
    messages_to_drop = messages[start_idx : start_idx + num_to_drop]
    drop_commands = [RemoveMessage(id=msg.id) for msg in messages_to_drop if msg.id]
    
    # Send texts to Celery for Tier 2 Extraction
    texts_to_extract = [msg.content for msg in messages_to_drop if isinstance(msg.content, str)]
    
    user_id = config.get("configurable", {}).get("user_id", "default_user")
    trip_id = config.get("configurable", {}).get("thread_id", "default_trip")
    
    if texts_to_extract:
        # Fire and forget async Celery task
        process_evicted_memory.delay(texts_to_extract, user_id, trip_id)
        
    return {"messages": drop_commands}

def build_graph(checkpointer: AsyncPostgresSaver = None):
    # initial graph with specific state (memory)
    builder = StateGraph(AgentState)

    # add our nodes
    builder.add_node("rag_injector", inject_memories)
    builder.add_node("planner", plan_itinerary)
    builder.add_node("agent", call_gemini)
    builder.add_node("tools", ToolNode([add_stop, remove_stop, update_stop, move_stop_between_days]))
    builder.add_node("validator", validate_tool_call)
    builder.add_node("critic", evaluate_itinerary)
    builder.add_node("memory_manager", memory_manager)

    # draw the entry edge -> goes to RAG injector first
    builder.add_edge(START, "rag_injector")
    
    # RAG -> Planner -> Agent
    builder.add_edge("rag_injector", "planner")
    builder.add_edge("planner", "agent")

    # conditional edge from agent
    builder.add_conditional_edges("agent", route_from_agent)
    
    # conditional edge from validator
    builder.add_conditional_edges("validator", router_from_validator)

    # conditional edge from critic
    builder.add_conditional_edges("critic", route_from_critic)
    
    # after tools finish executing, we go back to the agent to summarize or use more tools
    builder.add_edge("tools", "agent")
    
    # memory manager always ends
    builder.add_edge("memory_manager", END)

    return builder.compile(checkpointer=checkpointer, interrupt_before=["tools"])
