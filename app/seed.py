"""Seed the database with fake users (idempotent). Development only."""

import asyncio
import os
import sys

from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import async_session_maker
from app.models.enums import UserRole
from app.models.user import User


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"Missing required env var: {name}", file=sys.stderr)
        sys.exit(1)
    return value


async def seed() -> None:
    """Create seed users if they do not already exist. Development only."""
    if settings.APP_ENV != "development":
        print("Refusing to seed: APP_ENV must be 'development'", file=sys.stderr)
        sys.exit(1)
    users = [
        ("admin", UserRole.ADMIN, settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD),
        (
            "loan_officer",
            UserRole.LOAN_OFFICER,
            "officer@example.com",
            _require_env("SEED_LOAN_OFFICER_PASSWORD"),
        ),
        (
            "applicant",
            UserRole.APPLICANT,
            "applicant@example.com",
            _require_env("SEED_APPLICANT_PASSWORD"),
        ),
    ]
    async with async_session_maker() as session:
        for _name, role, email, password in users:
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
