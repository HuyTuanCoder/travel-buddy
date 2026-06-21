from langchain_core.messages import SystemMessage, HumanMessage
import logging
from src.schemas.agent import AgentState
from src.memory.embeddings import embed_text
from src.memory.vector_db import search_memories

logger = logging.getLogger(__name__)

def inject_memories(state: AgentState, config: dict):
    """
    RAG Injector Node: Runs before the LLM.
    Embeds the user's latest message, searches Qdrant for semantic and deterministic facts,
    and injects them into the state as a SystemMessage.
    """
    messages = state.get("messages", [])
    if not messages:
        return {}

    # Get the latest message text
    latest_message = messages[-1]
    
    # We only inject RAG for Human messages, skip if it's a Tool or AI message
    if not isinstance(latest_message, HumanMessage):
        return {}
        
    query_text = latest_message.content
    user_id = config.get("configurable", {}).get("user_id", "default_user")

    try:
        # Embed the query
        logger.info("Embedding latest user query for RAG...")
        vector = embed_text(query_text)
        
        # Search long-term memory
        logger.info(f"Searching Qdrant for memories related to: {query_text[:50]}...")
        memories = search_memories(vector, user_id=user_id, limit=5)
        
        if memories:
            # Format the memories into a system prompt
            memory_context = "--- Long Term Memories ---\n"
            for mem in memories:
                if mem.get("category") == "GENERAL_MEMORY":
                    memory_context += f"- Relevant Past Story: {mem.get('raw_quote')}\n"
                else:
                    memory_context += f"- {mem.get('permanence')} Constraint ({mem.get('category')}): {mem.get('topic')}. User Sentiment: {mem.get('sentiment')}. Raw quote: '{mem.get('raw_quote')}'\n"
                    
            system_msg = SystemMessage(content=memory_context)
            logger.info(f"Injected {len(memories)} memories into context.")
            
            # Note: We don't overwrite messages, we just append the SystemMessage.
            # In a real setup, we might inject this at the *start* of the message array,
            # but appending it before the LLM node also works.
            return {"messages": [system_msg]}
    except Exception as e:
        logger.error(f"Failed to inject RAG memories: {e}")
        
    return {}
