from langgraph.graph import StateGraph, START, END
from src.agent.state import AgentState
from src.agent.nodes.gemini import call_gemini

from langgraph.prebuilt import ToolNode, tools_condition
from src.agent.tools.itinerary import add_stop_to_day

def build_graph():
    # initial graph with specific state (memory)
    builder = StateGraph(AgentState)

    # add our nodes
    builder.add_node("agent", call_gemini)
    builder.add_node("tools", ToolNode([add_stop_to_day]))

    # draw the entry edge
    builder.add_edge(START, "agent")

    # conditional edge
    # if the llm decids it needs to use tool => go to "tools" node
    # otherwise go to "END"
    builder.add_conditional_edges("agent", tools_condition)

    # complete the loop, after tools we go straight back to agent
    # literally like drawing a graph
    builder.add_edge("tools", "agent")

    return builder.compile()
