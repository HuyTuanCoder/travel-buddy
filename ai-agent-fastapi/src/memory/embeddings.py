from sentence_transformers import SentenceTransformer
import os
import logging

logger = logging.getLogger(__name__)

# Load the model directly from the HuggingFace cache baked into the Docker image
# We use a singleton pattern so it only loads into RAM once per worker process.
_model = None

def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading SentenceTransformer ('all-MiniLM-L6-v2') into RAM...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def embed_text(text: str) -> list[float]:
    """
    Converts text into a 384-dimensional vector array.
    Runs locally on CPU for zero cost.
    """
    model = get_embedding_model()
    # model.encode returns a numpy array, we need to convert it to a python list for Qdrant
    vector = model.encode(text)
    return vector.tolist()

def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Reach Goal: Batch processing for massive documents.
    """
    model = get_embedding_model()
    vectors = model.encode(texts)
    return [v.tolist() for v in vectors]
