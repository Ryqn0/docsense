import os

from sqlalchemy.ext.asyncio import (
    async_sessionmaker,  # factory that creates AsyncSession instances
    create_async_engine,  # async version of create_engine
)
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://docsense:docsense_dev_password@postgres:5432/docsense",
)
# Fallback default for running outside Docker
# In Docker, the real value comes from .env via docker-compose

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # True = print every SQL query (useful for debugging)
    pool_size=10,  # max persistent connections in the pool
    max_overflow=20,  # extra connections allowed above pool_size under load
)
# Connection pooling: instead of opening/closing a DB connection per request
# (expensive: ~5-10ms each), we keep a pool of open connections and reuse them
# pool_size=10 * max_overflow=20 = up to 30 simultaneous DB connections

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    # expire_on_commit=Fakse: after commit(), ORM objects stay usable
    # Default (True) would make objects invalid after commit - confusing in APIs
)


class Base(DeclarativeBase):
    pass


# DeclarativeBase: the parent class all our models will inherit from
# SQLAlchemy uses this to discover tables and their relationships
# All models in models.py will do: cmass Tenant(Base): ...


async def get_db():
    """FastAPI dependency - yields a database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # yield = this is a generator
            # FastAPI calls everything before yield (open session)
            # runs the endpoint function
            # then calls everything after yield (close session)
            await session.commit()
        except Exception:
            await session.rollback()
            # If anything goes wrong, roll back all changes in this request
            # Atomic: either everything succeeds or nothing does
            raise


# get_db is a FastAPI dependency - endpoints declare it like:
# async def my_endpoint(db: AsyncSession = Depends(get_db)):
# FastAPI automatically manages the session lifecycle
