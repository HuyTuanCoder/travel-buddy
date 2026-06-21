from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # 1. The Conversation History
    # 'add_messages' ensures that when a new node returns a message, 
    # it appends it to the list instead of overwriting the whole list.
    messages: Annotated[list[AnyMessage], add_messages]
    
    # 2. Agentic Planning
    # The Planner Node will write a step-by-step string here (e.g., "1. Find hotel 2. Book flight").
    # The main Agent will read this so it doesn't get lost.
    plan: str
    
    # 3. Reflection / Validation
    # If the Pydantic Validator catches bad JSON, it will drop the error string here.
    # The Gemini node will read this on the next loop and fix its mistake.
    validation_error: str
