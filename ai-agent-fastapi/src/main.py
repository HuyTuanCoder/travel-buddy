from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.core.telemetry import setup_telemetry

setup_telemetry()

from src.api.chat_routes import router as chat_router
from src.core.database import DATABASE_URL

@asynccontextmanager
async def lifespan(app: FastAPI):
    psycopg_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    async with AsyncPostgresSaver.from_conn_string(psycopg_url) as checkpointer:
        await checkpointer.setup()
        print("✅ LangGraph Checkpointer tables verified in Postgres!")
        
    from src.core.database import engine, Base
    import src.schemas.database # Ensure models are loaded
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Custom Database tables (ChatHistory, etc) verified in Postgres!")
        
    yield
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

@app.post("/ai/test-echo")
async def test_echo(request: Request):
    body = await request.body()
    headers = dict(request.headers)
    return {"headers": headers, "body_length": len(body), "body": body.decode('utf-8', errors='replace')}
