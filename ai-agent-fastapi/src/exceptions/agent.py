from src.exceptions.base import TravelBuddyError

class AgentSystemError(TravelBuddyError):
    """Base class for errors originating from the core LangGraph agent."""
    pass

class LLMCoreError(AgentSystemError):
    """
    Provider outages, Context Window Limits, or Safety Filter blocks.
    This is fatal to the graph's execution and will trigger the Emergency Fallback LLM.
    """
    pass

class GraphStateError(AgentSystemError):
    """
    Corrupt LangGraph states, failed Pydantic validator nodes, or unparseable JSON schemas.
    This halts graph execution and triggers the Emergency Fallback.
    """
    pass
