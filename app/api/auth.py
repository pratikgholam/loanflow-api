"""Authentication routes: register and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.rate_limit import rate_limit_login, rate_limit_register
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import authenticate_user, login_token, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_register)],
)
async def register(user_in: UserCreate, session: AsyncSession = Depends(get_session)):
    """Register a new applicant account."""
    try:
        user = await register_user(session, user_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return user


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(rate_limit_login)],
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    """Authenticate with email (as username) and password, return a JWT."""
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=login_token(user))
