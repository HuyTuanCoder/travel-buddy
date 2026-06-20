from fastapi import APIRouter
from pydantic import BaseModel
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.agent.graph import build_graph
from src.core.database import DATABASE_URL

router = APIRouter()

class ChatRequest(BaseModel):
    trip_id: str
    message: str

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
        # compile graph with checkpointer to save state
        app_graph = build_graph(checkpointer)

        # create the input for the model
        inputs = {"messages": [("user", request.message)]}

        # tell langgraph which memory row to pull from postgres
        config = {"configurable": {"thread_id": request.trip_id}}

        # run graph asynchronously, because of db pull
        final_state = await app_graph.ainvoke(inputs, config=config)

        ai_response = final_state["messages"][-1].content

    return {"reply": ai_response}