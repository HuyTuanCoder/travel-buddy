from celery import shared_task
import logging
import asyncio
from src.memory.extractor import extract_from_messages
from src.memory.vector_db import upsert_fact
from src.memory.embeddings import embed_text

logger = logging.getLogger(__name__)

async def _process_evicted_memory(messages: list[str], user_id: str, trip_id: str):
    """
    Async implementation of the memory eviction process.
    """
    try:
        logger.info(f"Processing {len(messages)} evicted messages for memory extraction...")
        
        # 1. Extract facts (hybrid spaCy/Gemini pipeline)
        facts = extract_from_messages(messages)
        
        # 2. Embed and Upsert each fact
        for fact in facts:
            # Embed the raw quote for semantic search later
            vector = embed_text(fact.raw_quote)
            
            # Upsert into Qdrant (using deterministic UUIDs for permanent facts)
            upsert_fact(fact, user_id, trip_id, vector)
            
        logger.info(f"Successfully saved {len(facts)} facts to long-term memory.")
    except Exception as e:
        logger.error(f"Failed to process evicted memory: {e}")

@shared_task(name="process_evicted_memory")
def process_evicted_memory(messages: list[str], user_id: str, trip_id: str):
    """
    Celery task that runs the async memory extraction pipeline.
    This is completely decoupled from the main LangGraph execution.
    """
    asyncio.run(_process_evicted_memory(messages, user_id, trip_id))
