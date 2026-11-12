"""User management routes (admin)."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_admin
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserRead], dependencies=[Depends(require_admin)])
async def list_users(session: AsyncSession = Depends(get_session)):
    """List all users (admin only)."""
    result = await session.execute(select(User))
    return result.scalars().all()


@router.get(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_admin)],
)
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    """Get a user by id (admin only)."""
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_admin)],
)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a user's role/is_active (admin only)."""
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    await session.commit()
    await session.refresh(user)
    return user
