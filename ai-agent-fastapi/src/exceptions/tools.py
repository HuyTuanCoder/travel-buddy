from src.exceptions.base import TravelBuddyError

class ToolExecutionError(TravelBuddyError):
    """Base class for any error occurring inside an agent tool."""
    pass

class ToolAPIError(ToolExecutionError):
    """
    External dependency failures (e.g., Maps API timeout, Tavily 500).
    These are routed to DevOps monitoring/logging and may trigger Celery retries.
    """
    pass

class ToolValidationError(ToolExecutionError):
    """
    LLM hallucinated bad arguments (e.g., Pydantic validation failure).
    This is normal LLM behavior. It does NOT alert DevOps, but silently
    feeds the error string back to the LLM for self-correction.
    """
    pass
