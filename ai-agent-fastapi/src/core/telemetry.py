import os
import json
import logging
import structlog
import redis.asyncio as aioredis

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Singleton async Redis client for PubSub streaming
# Prevents connection leaks from nodes creating a new client on every call.
# ---------------------------------------------------------------------------
_redis_client: aioredis.Redis | None = None

async def _get_redis() -> aioredis.Redis:
    """Lazily create and cache a single async Redis connection."""
    global _redis_client
    if _redis_client is None:
        from src.core.config import settings
        _redis_client = aioredis.from_url(settings.REDIS_URL)
    return _redis_client

async def close_telemetry_redis() -> None:
    """Explicitly close the global Redis connection pool to prevent socket leaks."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose() if hasattr(_redis_client, "aclose") else await _redis_client.close()
        _redis_client = None


async def publish_thought(channel: str, content: str) -> None:
    """Stream a blockquote '> thought' bubble to the frontend."""
    r = await _get_redis()
    await r.publish(channel, json.dumps({"type": "thought", "content": content}))


async def publish_token(channel: str, content: str) -> None:
    """Stream a raw LLM token to the frontend."""
    r = await _get_redis()
    await r.publish(channel, json.dumps({"type": "token", "content": content}))


async def publish_event(channel: str, event_type: str, content: str) -> None:
    """Stream any arbitrary event type (done, error, draft_update, tool_call)."""
    r = await _get_redis()
    await r.publish(channel, json.dumps({"type": event_type, "content": content}))


# ---------------------------------------------------------------------------
# Structlog Configuration
# ---------------------------------------------------------------------------
def setup_telemetry():
    """
    Configures structlog for the application.
    Uses JSON rendering for production and colorful text rendering for local dev.
    """
    env = os.getenv("ENV", "development")
    
    # Configure the standard logging module to route to structlog
    logging.basicConfig(
        format="%(message)s",
        stream=None,
        level=logging.INFO,
    )
    
    # Processors applied to all log entries
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            # If in dev, pretty print. If in prod, print JSON.
            structlog.dev.ConsoleRenderer(colors=True) if env == "development" else structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
