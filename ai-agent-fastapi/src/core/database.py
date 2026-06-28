import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from src.core.config import settings

from sqlalchemy.pool import NullPool

# get the database url from env
DATABASE_URL = settings.DATABASE_URL

# create the engine that manage connection pool to postgres
is_dev = settings.ENV == "development"

# Celery prefork workers cannot share async event loops
is_celery = os.getenv("IS_CELERY_WORKER") == "true"
engine_kwargs = {"echo": is_dev}
if is_celery:
    engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

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