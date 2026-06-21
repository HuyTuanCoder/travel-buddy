import os
import logging
import structlog

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
