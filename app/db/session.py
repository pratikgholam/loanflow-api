"""Async SQLAlchemy 2.0 engine, session factory, and session dependency."""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_session() -> AsyncSession:
    """Yield an async SQLAlchemy session (FastAPI dependency)."""
    async with async_session_maker() as session:
        yield session
