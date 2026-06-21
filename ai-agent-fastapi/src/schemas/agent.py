from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # 1. The Conversation History
    # 'add_messages' ensures that when a new node returns a message, 
    # it appends it to the list instead of overwriting the whole list.
    messages: Annotated[list[AnyMessage], add_messages]
    
    # 2. Agentic Planning
    # The Planner Node generates a strict checklist of actions.
    plan: list[str]
    
    # 3. Reflection / Validation
    # If the Pydantic Validator catches bad JSON, it will drop the error string here.
    validation_error: str
    
    # 4. Critic Feedback (Linear CoT)
    # The Critic Node evaluates the itinerary. If it fails, feedback is placed here.
    critic_feedback: str
    
    # 5. Failsafe Retry Count
    # Prevents infinite loops between Agent and Critic.
    retry_count: int
