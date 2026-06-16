from langchain_google_genai import ChatGoogleGenerativeAI
from src.agent.state import AgentState
from src.agent.tools.itinerary import add_stop_to_day

llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest")

tools = [add_stop_to_day]
llm_with_tools = llm.bind_tools(tools)

def call_gemini(state: AgentState):
    # read messages from the state
    messages = state["messages"]

    # pass to llm
    response = llm_with_tools.invoke(messages)

    # return new messages to be appended to state
    return {"messages": [response]}
    