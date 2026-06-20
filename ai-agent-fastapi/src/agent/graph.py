from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.agent.state import AgentState
from src.agent.nodes.gemini import call_gemini
from src.agent.nodes.validator import validate_tool_call
from src.agent.tools.itinerary import add_stop, remove_stop, update_stop, move_stop_between_days

# custom router to check if llm try to call a tool
def route_from_agent(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "validator"
    return END

# custom router to check if Pydantic reject the json
def router_from_validator(state: AgentState):
    if state.get("validation_error"):
        return "agent" # bounce back to llm
    return "tools" # get to tool calls

def build_graph(checkpointer: AsyncPostgresSaver = None):
    # initial graph with specific state (memory)
    builder = StateGraph(AgentState)

    # add our nodes
    builder.add_node("agent", call_gemini)
    builder.add_node("tools", ToolNode([add_stop, remove_stop, update_stop, move_stop_between_days]))
    builder.add_node("validator", validate_tool_call)

    # draw the entry edge
    builder.add_edge(START, "agent")

    # conditional edge
    # if the llm decides it needs to use tool => go to "tools" node
    # otherwise go to "END"
    builder.add_conditional_edges("agent", route_from_agent)
    builder.add_conditional_edges("validator", router_from_validator)

    # complete the loop, after tools we go straight back to agent
    # literally like drawing a graph
    builder.add_edge("tools", "agent")

    # when invoke the model => it create blank dict on server ram then delete after run
    # we inhject a postgres saver into graph compiler so it knows the last state
    # of user conversation, if not it create a blank one, then upsert to postgres
    return builder.compile(checkpointer=checkpointer)
