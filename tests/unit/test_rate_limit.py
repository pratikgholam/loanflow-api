"""Unit tests for the in-memory rate limiter (no DB required)."""

from app.core.rate_limit import RateLimiter


def test_allows_up_to_limit_then_blocks():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    assert limiter.allow("user-a") is True
    assert limiter.allow("user-a") is True
    assert limiter.allow("user-a") is True
    assert limiter.allow("user-a") is False


def test_different_keys_are_independent():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    assert limiter.allow("user-a") is True
    assert limiter.allow("user-a") is False
    assert limiter.allow("user-b") is True


def test_reset_clears_state():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    assert limiter.allow("user-a") is True
    assert limiter.allow("user-a") is False
    limiter.reset()
    assert limiter.allow("user-a") is True
