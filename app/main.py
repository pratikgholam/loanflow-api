"""FastAPI application factory and entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.users import router as users_router
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Dispose the async engine on shutdown."""
    yield
    await engine.dispose()


app = FastAPI(title="LoanFlow API", lifespan=lifespan)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
