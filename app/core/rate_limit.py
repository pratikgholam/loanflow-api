"""In-memory fixed-window rate limiter for auth endpoints."""

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status


class RateLimiter:
    """Fixed-window in-memory rate limiter.

    shortcut: in-memory store (single process); upgrade to Redis for multiple
    workers or when behind a proxy.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            window = [t for t in self._hits[key] if now - t < self.window_seconds]
            self._hits[key] = window
            if len(window) >= self.max_requests:
                return False
            window.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


_login_limiter = RateLimiter(max_requests=5, window_seconds=60)
_register_limiter = RateLimiter(max_requests=3, window_seconds=60)


async def rate_limit_login(request: Request) -> None:
    key = request.client.host if request.client else "anonymous"
    if not _login_limiter.allow(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests"
        )


async def rate_limit_register(request: Request) -> None:
    key = request.client.host if request.client else "anonymous"
    if not _register_limiter.allow(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests"
        )


def reset_limiters() -> None:
    """Clear limiter state (used by tests for isolation)."""
    _login_limiter.reset()
    _register_limiter.reset()
