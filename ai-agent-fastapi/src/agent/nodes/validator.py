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
        
    bounce_backs = []
    has_error = False
    
    for tool_call in last_message.tool_calls:
        try:
            # In Milestone 6, we will actually parse tool_call["args"] into a Pydantic model here!
            # For now, we assume it's valid.
            pass
            
            # If valid, we still need to provide a dummy ToolMessage if we are bouncing back others?
            # Actually, LangGraph allows Agent to just fix the whole thing, but we must return ToolMessages for ALL tool_calls.
        except ValidationError as e:
            has_error = True
            error_msg = f"Your JSON is invalid. Fix these Pydantic errors: {str(e)}"
            bounce_backs.append(ToolMessage(
                content=error_msg,
                tool_call_id=tool_call["id"],
                name=tool_call["name"]
            ))
        except Exception as e:
            has_error = True
            bounce_backs.append(ToolMessage(
                content=f"Error parsing tool call: {str(e)}",
                tool_call_id=tool_call["id"],
                name=tool_call["name"]
            ))
            
    if has_error:
        # If any tool failed, we must ensure EVERY tool call in the list has a ToolMessage response
        # so LangGraph doesn't crash with MissingToolCall errors.
        final_bounce_backs = []
        for tool_call in last_message.tool_calls:
            # Check if we already generated an error for this tool
            existing = next((b for b in bounce_backs if b.tool_call_id == tool_call["id"]), None)
            if existing:
                final_bounce_backs.append(existing)
            else:
                final_bounce_backs.append(ToolMessage(
                    content="Cancelled because a parallel tool call failed validation. Fix the errors and try again.",
                    tool_call_id=tool_call["id"],
                    name=tool_call["name"]
                ))
        return {"messages": final_bounce_backs, "validation_error": "Pydantic validation failed on one or more tools."}

    # If it passes validation, clear the error state
    return {"validation_error": ""}
