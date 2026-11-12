"""Unit tests for the seed script's development-only guard (no DB required)."""

import asyncio

import app.seed


def test_refuses_non_development(monkeypatch):
    monkeypatch.setattr(app.seed.settings, "APP_ENV", "production")
    try:
        asyncio.run(app.seed.seed())
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("expected SystemExit when APP_ENV is not development")


def test_missing_required_env_exits(monkeypatch):
    monkeypatch.setattr(app.seed.settings, "APP_ENV", "development")
    monkeypatch.delenv("SEED_LOAN_OFFICER_PASSWORD", raising=False)
    monkeypatch.delenv("SEED_APPLICANT_PASSWORD", raising=False)
    try:
        asyncio.run(app.seed.seed())
    except SystemExit as exc:
        assert exc.code == 1
    else:
        raise AssertionError("expected SystemExit when required env vars are missing")
