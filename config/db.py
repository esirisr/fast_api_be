import os
from collections.abc import AsyncIterator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from server.models.base import Base

engine = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


async def init_db(database_url: str | None = None):
    global engine, SessionLocal

    raw_url = database_url or os.getenv("DATABASE_URL")
    if not raw_url:
        raise RuntimeError("DATABASE_URL is not defined.")

    url = make_url(raw_url)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+asyncpg")

    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        from server.models.Payment import Payment
        from server.models.User import User

        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    except Exception:
        await engine.dispose()
        engine = None
        SessionLocal = None
        raise


async def close_db():
    global engine, SessionLocal
    if engine is not None:
        await engine.dispose()
    engine = None
    SessionLocal = None


async def get_db() -> AsyncIterator[AsyncSession]:
    if SessionLocal is None:
        raise RuntimeError("Database has not been initialized.")
    async with SessionLocal() as session:
        yield session
