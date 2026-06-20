from pydantic import ValidationError
from langchain_core.messages import ToolMessage
from src.agent.state import AgentState

def validate_tool_call(state: AgentState):
    """
    This node intercepts Gemini's tool calls BEFORE they execute.
    If Gemini hallucinates bad JSON, we bounce it back with the exact error.
    """
    last_message = state["messages"][-1]
    
    # If the LLM didn't try to call a tool, just pass it through
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {"validation_error": ""}
        
    for tool_call in last_message.tool_calls:
        try:
            # In Milestone 6, we will actually parse tool_call["args"] into a Pydantic model here!
            # For now, we assume it's valid.
            pass
            
        except ValidationError as e:
            # THE MAGIC: We caught a hallucination!
            # We create a fake ToolMessage that pretends the tool crashed, 
            # and we send the exact Pydantic error back to Gemini so it can fix it.
            error_msg = f"Your JSON is invalid. Fix these Pydantic errors: {str(e)}"
            
            bounce_back = ToolMessage(
                content=error_msg,
                tool_call_id=tool_call["id"],
                name=tool_call["name"]
            )
            
            # We append the error to the state so Gemini reads it on the next loop!
            return {"messages": [bounce_back], "validation_error": str(e)}

    # If it passes validation, clear the error state
    return {"validation_error": ""}
