from contextlib import asynccontextmanager
from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.core.telemetry import setup_telemetry

setup_telemetry()

from src.api.chat_routes import router as chat_router
from src.core.database import DATABASE_URL

# This function runs exactly once when the server boots up
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to Postgres (psycopg doesn't understand +asyncpg)
    psycopg_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    async with AsyncPostgresSaver.from_conn_string(psycopg_url) as checkpointer:
        # This tells LangGraph to execute the CREATE TABLE scripts if they don't exist yet!
        await checkpointer.setup()
        print("✅ LangGraph Checkpointer tables verified in Postgres!")
    
    yield  # The server is now running!
    
    print("🛑 Server shutting down...")

app = FastAPI(
    title="Travel Buddy AI",
    description="LangGraph Agent orchestration layer",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(chat_router, prefix="/ai")

@app.get("/")
def health_check():
    return {"status": "AI is alive and breathing."}
