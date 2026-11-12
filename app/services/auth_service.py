"""Authentication service: registration, login, password, JWT."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserRead


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def register_user(session: AsyncSession, user_in: UserCreate) -> UserRead:
    """Register a new applicant user. Raises ValueError if email exists."""
    existing = await get_user_by_email(session, user_in.email)
    if existing:
        raise ValueError("Email already registered")
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=UserRole.APPLICANT,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserRead.model_validate(user)


async def authenticate_user(
    session: AsyncSession, email: str, password: str
) -> Optional[User]:
    """Verify credentials and return the user, or None if invalid."""
    user = await get_user_by_email(session, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def login_token(user: User) -> str:
    """Issue a JWT access token for the authenticated user."""
    return create_access_token(data={"sub": user.email})


def user_to_read(user: User) -> UserRead:
    return UserRead.model_validate(user)
