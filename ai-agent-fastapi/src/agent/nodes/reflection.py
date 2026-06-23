import structlog
from langchain_core.messages import AIMessage
from src.schemas.agent import AgentState
from src.core.config import get_llm
from src.core.telemetry import publish_thought

logger = structlog.get_logger(__name__)

async def reflection_node(state: AgentState, config: dict):
    """
    Post-Execution Reflection Node.
    Intercepts failed or empty tool executions and uses a low-temperature LLM
    to generate a pivot directive, preventing infinite retry loops.
    """
    messages = state.get("messages", [])
    if not messages:
        return state
        
    last_message = messages[-1]
    tool_call_id = getattr(last_message, "tool_call_id", "unknown")
    tool_name = getattr(last_message, "name", "unknown")
    tool_content = str(last_message.content)
    
    logger.warning(f"Tool {tool_name} failed or returned empty result. Triggering reflection.")
    
    prompt = f"""You are an expert AI Supervisor debugging an autonomous agent.
The agent just called the tool '{tool_name}' and it returned the following failure or empty result:

{tool_content}

The agent has a tendency to mindlessly retry the exact same failing tool call in an infinite loop.
Look at the failure and generate a concise 1-sentence directive commanding the agent on how it MUST pivot its strategy. Do not execute tools. Just output the directive.
"""

    if tool_name == "search_past_conversations":
        prompt += "\nSPECIAL RULE FOR MEMORY: Since this was a memory search that returned no results, DO NOT instruct the agent to retry. Instruct the agent to stop searching, apologize to the user, and ask them to clarify what they said."
    
    # Use low temperature for deterministic reflection
    llm = get_llm().with_config({"temperature": 0.2})
    
    logger.info("Reflection Node: Generating pivot directive...")
    response = await llm.ainvoke(prompt)
    
    thread_id = config.get("configurable", {}).get("thread_id", "")
    if thread_id:
        await publish_thought(f"stream:{thread_id}", f"\n\n> SUPERVISOR INTERVENTION:\n> {response.content}\n")
    
    directive = f"[SUPERVISOR DIRECTIVE for tool {tool_name}]: {response.content}"
    logger.info(f"Reflection Node: {directive}")
    
    return {"messages": [AIMessage(content=directive, name="reflection")]}
