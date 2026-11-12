"""Seed the database with fake users (idempotent). Fake data only."""

import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import async_session_maker
from app.models.enums import UserRole
from app.models.user import User

SEED_USERS = [
    ("admin", UserRole.ADMIN, settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD),
    (
        "loan_officer",
        UserRole.LOAN_OFFICER,
        "officer@example.com",
        "officer-secret-change-me",
    ),
    (
        "applicant",
        UserRole.APPLICANT,
        "applicant@example.com",
        "applicant-secret-change-me",
    ),
]


async def seed() -> None:
    """Create seed users if they do not already exist."""
    async with async_session_maker() as session:
        for _name, role, email, password in SEED_USERS:
            result = await session.execute(select(User).where(User.email == email))
            if result.scalar_one_or_none() is not None:
                continue
            session.add(
                User(
                    email=email,
                    hashed_password=get_password_hash(password),
                    role=role,
                    is_active=True,
                )
            )
        await session.commit()


def main() -> None:
    """Entry point for `python -m app.seed`."""
    asyncio.run(seed())


if __name__ == "__main__":
    main()
