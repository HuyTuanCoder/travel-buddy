import structlog
import json
from langchain_core.messages import SystemMessage, HumanMessage
from src.schemas.agent import AgentState
from src.core.config import get_llm
from langchain_core.runnables import RunnableConfig

logger = structlog.get_logger(__name__)

async def call_speaker(state: AgentState, config: RunnableConfig):
    """
    Gate 3: The Speaker Agent.
    Has no tools. Reads the final state and generates the definitive final response for the user.
    """
    llm = get_llm()
    
    messages = state.get("messages", [])
    itinerary_draft = state.get("itinerary_draft", [])
    
    sys_msg = SystemMessage(content="You are a helpful travel assistant finalizing a conversation with the user.")
    
    ephemeral_context = "\n--- SYSTEM EXECUTION CONTEXT ---\n"
    ephemeral_context += "You have just finished using your tools in the background to fulfill the user's request.\n"
    
    rag_context = state.get("rag_context", "")
    if rag_context:
        ephemeral_context += f"\nKNOWN CONSTRAINTS & MEMORIES:\n{rag_context}\n"
        
    running_summary = state.get("running_summary", "")
    if running_summary:
        ephemeral_context += f"\nPREVIOUS EVENTS (Summary of dropped messages):\n{running_summary}\n"
        
    if itinerary_draft:
        ephemeral_context += f"\nTHE CURRENT ITINERARY DRAFT IS:\n{json.dumps(itinerary_draft, indent=2)}\n"
    ephemeral_context += "\nBased on the conversation and the work you just completed, provide the final response to the user. DO NOT attempt to call any tools."
    
    filtered_history = [msg for msg in messages if not isinstance(msg, SystemMessage)]
    
    invoke_messages = [sys_msg] + filtered_history + [HumanMessage(content=ephemeral_context)]
    
    logger.info("Speaker Node: Generating final response...")
    response = await llm.ainvoke(invoke_messages, config)
    
    return {
        "messages": [response]
    }
