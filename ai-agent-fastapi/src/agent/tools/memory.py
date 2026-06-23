from langchain_core.tools import tool
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel, Field
from typing import Optional
import structlog
import json

from src.memory.vector_db import search_memories
from src.memory.embeddings import embed_text

logger = structlog.get_logger(__name__)

class SearchFilters(BaseModel):
    semantic_query: str = Field(description="The semantic concept to search for (e.g., 'BBQ restaurant' or 'cool waterfall').")
    time_range_days: Optional[int] = Field(description="Optional. If the user says 'yesterday' or '3 days ago', enter the number of days to temporally filter the results. E.g. 'yesterday' = 1.")

@tool("search_past_conversations", args_schema=SearchFilters)
def search_past_conversations(semantic_query: str, time_range_days: Optional[int] = None, config: RunnableConfig = None) -> str:
    """
    Actively query the user's long-term memory banks. 
    Use this tool when the user references a past conversation, a past preference, or says things like 'remember what I told you'.
    """
    logger.info(f"Agentic Memory Retrieval: Searching '{semantic_query}' with temporal filter: {time_range_days} days")
    
    user_id = config.get("configurable", {}).get("user_id", "default_user") if config else "default_user"

    try:
        vector = embed_text(semantic_query)
        memories = search_memories(vector, user_id=user_id, limit=3, time_range_days=time_range_days)
        
        if not memories:
            return "[]"
            
        formatted_memories = []
        for mem in memories:
            if mem.get("category") == "GENERAL_MEMORY":
                formatted_memories.append(f"- Relevant Past Story: {mem.get('raw_quote')}")
            else:
                formatted_memories.append(f"- {mem.get('permanence')} Constraint ({mem.get('category')}): {mem.get('topic')}. User Sentiment: {mem.get('sentiment')}. Raw quote: '{mem.get('raw_quote')}'")
                
        return json.dumps(formatted_memories, indent=2)
        
    except Exception as e:
        logger.error(f"Memory retrieval failed: {e}")
        return "[]"
