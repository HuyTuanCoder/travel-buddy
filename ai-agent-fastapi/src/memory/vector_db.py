from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import uuid
import os
import logging
from src.schemas.memory import ExtractedFact

logger = logging.getLogger(__name__)

# We read the Qdrant host from env vars, falling back to localhost for local dev outside Docker
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "travel_buddy_memory"

_client = None

def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        logger.info(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
        _client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        # Ensure collection exists
        if not _client.collection_exists(collection_name=COLLECTION_NAME):
            _client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")
    return _client

def upsert_fact(fact: ExtractedFact, user_id: str, trip_id: str, vector: list[float]):
    """
    Overwrites structured facts using a deterministic UUID to prevent hallucinated duplicates.
    """
    client = get_qdrant_client()
    
    # Deterministic UUID generation: hash of (user_id + category) for PERMANENT facts
    # For TEMPORARY facts, we hash (trip_id + category)
    if fact.permanence.value == "PERMANENT":
        hash_string = f"user_{user_id}_category_{fact.category.value}"
    else:
        hash_string = f"trip_{trip_id}_category_{fact.category.value}"
        
    # Generate UUID5 based on a custom namespace (using DNS as dummy namespace)
    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, hash_string))
    
    payload = fact.model_dump()
    payload["user_id"] = user_id
    payload["trip_id"] = trip_id
    
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
        ]
    )
    logger.info(f"Upserted fact {fact.category.value} into Qdrant point {point_id}")

def search_memories(query_vector: list[float], user_id: str, limit: int = 5) -> list[dict]:
    """
    Performs pure semantic text embedding search across unstructured memories.
    """
    client = get_qdrant_client()
    
    search_result = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="user_id",
                    match=MatchValue(value=user_id)
                )
            ]
        ),
        limit=limit
    )
    
    return [hit.payload for hit in search_result]
