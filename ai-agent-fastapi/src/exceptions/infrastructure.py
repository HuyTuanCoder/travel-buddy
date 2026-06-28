from src.exceptions.base import TravelBuddyError

class InfrastructureError(TravelBuddyError):
    """Base class for infrastructure-level failures."""
    pass

class PersistenceError(InfrastructureError):
    """Postgres transaction failures or checkpointer sync issues."""
    pass

class TelemetryError(InfrastructureError):
    """
    Observability timeouts (e.g., Langfuse flush). 
    These must NEVER crash the main thread.
    """
    pass
