import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# get the database url from env
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# create the engine that manage connection pool to postgres
is_dev = ENVIRONMENT == "development"
engine = create_async_engine(DATABASE_URL, echo=is_dev)

# no global connection
# every time an API request comes
# => spawn lightweight session from this factory to talk to DB
# => then destroy it
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# base class, every python class inherit it will be converted into a Postgres table
Base = declarative_base()