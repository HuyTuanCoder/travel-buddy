"""
Base exceptions for the Travel Buddy AI Agent.
All custom exceptions inherit from TravelBuddyError.
"""

class TravelBuddyError(Exception):
    """Base class for all application-specific errors."""
    def __init__(self, message: str, original_exception: Exception = None, **context):
        super().__init__(message)
        self.message = message
        self.original_exception = original_exception
        self.context = context
        
    def __str__(self):
        ctx = f" (Context: {self.context})" if self.context else ""
        return f"{self.message}{ctx}"
