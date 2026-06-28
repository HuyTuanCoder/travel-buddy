from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.core.telemetry import setup_telemetry
from src.api.chat_routes import router as chat_router
from src.core.database import DATABASE_URL

setup_telemetry()

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

logger = structlog.get_logger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler to ensure all unhandled errors are logged via structlog
    and returned as a strict HTTP 500 JSON response, enforcing API discipline.
    """
    logger.error("Unhandled REST API Error", path=request.url.path, error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal system error occurred. It has been logged for investigation."}
    )

@app.post("/ai/test-echo")
async def test_echo(request: Request):
    body = await request.body()
    headers = dict(request.headers)
    return {"headers": headers, "body_length": len(body), "body": body.decode('utf-8', errors='replace')}
