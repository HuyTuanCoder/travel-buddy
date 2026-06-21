import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from langchain_google_vertexai import ChatVertexAI
import structlog

logger = structlog.get_logger(__name__)

class Settings(BaseSettings):
    # App Settings
    ENV: str = "development"
    AI_AGENT_PORT: int = 8007
    
    # Database
    DATABASE_URL: str
    
    # Message Brokers & Caching
    REDIS_URL: str
    RABBITMQ_URL: str
    
    # External Services
    QDRANT_URL: str
    GOOGLE_MAPS_API_KEY: str
    
    # Microservice gRPC
    ITINERARY_GRPC_URL: str
    LOCATION_GRPC_URL: str
    
    # GCP Vertex AI
    GCP_PROJECT_ID: str
    GCP_LOCATION: str
    
    # Observability
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # Ignore extra env vars not defined here
    )

# Instantiate the global settings object
settings = Settings()

def get_llm(model_name: str = "gemini-1.5-pro", temperature: float = 0) -> ChatVertexAI:
    """
    Factory function to instantiate the Vertex AI LLM.
    Uses centralized configuration.
    """
    logger.debug(f"Instantiating Vertex AI LLM: {model_name} in {settings.GCP_LOCATION}")
    return ChatVertexAI(
        model_name=model_name,
        temperature=temperature,
        project=settings.GCP_PROJECT_ID,
        location=settings.GCP_LOCATION,
        # GOOGLE_APPLICATION_CREDENTIALS must be set in the environment or Docker mount
    )
