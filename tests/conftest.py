"""Shared pytest fixtures: async test session, test client, seeded users per role."""

from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.session import get_session
from app.main import app
from app.models.base import Base
from app.models.enums import UserRole
from app.models.user import User


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Create the test schema on this test's loop, yield a session, drop it after."""
    engine = create_async_engine(settings.TEST_DATABASE_URL, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as sess:
        yield sess
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """ASGI test client bound to the test session (no running server needed)."""

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
async def users(session: AsyncSession) -> dict[str, User]:
    """Seed two applicants, one loan officer, one admin; keyed by role name."""
    rows = [
        ("applicant", UserRole.APPLICANT, "applicant@example.com"),
        ("applicant2", UserRole.APPLICANT, "applicant2@example.com"),
        ("loan_officer", UserRole.LOAN_OFFICER, "officer@example.com"),
        ("admin", UserRole.ADMIN, "admin@example.com"),
    ]
    for _name, role, email in rows:
        session.add(
            User(
                email=email,
                hashed_password=get_password_hash("password123"),
                role=role,
                is_active=True,
            )
        )
    await session.commit()
    result = await session.execute(select(User))
    db_users = {u.email: u for u in result.scalars().all()}
    return {name: db_users[email] for name, _, email in rows}


@pytest.fixture
def tokens(users: dict[str, User]) -> dict[str, str]:
    """Issue a JWT per seeded user."""
    return {
        name: create_access_token(data={"sub": user.email})
        for name, user in users.items()
    }
