from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AnyMessage

def get_conversational_transcript(messages: list[AnyMessage], turns: int = 3) -> str:
    """
    Extracts a clean transcript of the last `turns` conversational exchanges.
    Iterates backwards to skip noisy ToolMessage payloads and summarize them instead.
    This prevents the Planner and Critic from being 'blinded' by massive JSON blocks.
    """
    if not messages:
        return ""

    transcript_lines = []
    human_messages_seen = 0
    
    # Iterate backwards
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            human_messages_seen += 1
            if human_messages_seen > turns:
                break
            content = str(msg.content) if msg.content else ""
            transcript_lines.append(f"USER: {content}")
            
        elif isinstance(msg, AIMessage):
            content = str(msg.content) if msg.content else ""
            # If the AI just generated a tool call without content, note it
            if not content and hasattr(msg, 'tool_calls') and msg.tool_calls:
                tools = ", ".join([tc['name'] for tc in msg.tool_calls])
                transcript_lines.append(f"AGENT: [Requested Tools: {tools}]")
            elif content:
                transcript_lines.append(f"AGENT: {content}")
                
        elif isinstance(msg, ToolMessage):
            # Summarize the tool message instead of dumping the payload
            content_str = str(msg.content)
            content_preview = content_str[:100].replace('\n', ' ') + "..." if len(content_str) > 100 else content_str.replace('\n', ' ')
            name = getattr(msg, 'name', 'unknown_tool')
            transcript_lines.append(f"SYSTEM: [Tool '{name}' completed. Result: {content_preview}]")
            
    # Reverse back to chronological order
    transcript_lines.reverse()
    return "\n".join(transcript_lines)
