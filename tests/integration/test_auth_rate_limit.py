"""Integration tests for auth rate limiting against the test DB."""

import pytest

from app.core.rate_limit import reset_limiters


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    reset_limiters()


async def test_login_rate_limits_after_five_failures(client):
    """Login returns 429 after 5 failed attempts from the same client."""
    for _ in range(5):
        resp = await client.post(
            "/auth/login",
            data={"username": "x@example.com", "password": "wrong"},
        )
        assert resp.status_code == 401, resp.text
    resp = await client.post(
        "/auth/login",
        data={"username": "x@example.com", "password": "wrong"},
    )
    assert resp.status_code == 429, resp.text


async def test_register_rate_limits_after_three(client):
    """Register returns 429 after 3 attempts from the same client."""
    for i in range(3):
        resp = await client.post(
            "/auth/register",
            json={"email": f"user{i}@example.com", "password": "Password123"},
        )
        assert resp.status_code == 201, resp.text
    resp = await client.post(
        "/auth/register",
        json={"email": "user3@example.com", "password": "Password123"},
    )
    assert resp.status_code == 429, resp.text
