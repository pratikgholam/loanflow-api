# AGENTS.md

This file is a guide for AI coding agents working in the `loanflow-api` repo. It reflects what exists in the repo and what we have decided. Anything not yet built is marked **"planned"**. Keep this file accurate: update it whenever commands, structure, or rules change.

---

## 1. Project overview

`loanflow-api` is a loan application REST API.

- **Applicants** submit loan applications and can list/view only their own applications.
- **Loan officers** list/filter all applications and move their status (approve/reject, etc.).
- **Admins** manage users and roles (scope to be proposed in Phase 4).
- Every status change is recorded in a `loan_status_history` row, written in the same transaction as the status update.
- **Fake data only**: seed scripts use fake data. No real personal data anywhere.

Roles: `Applicant`, `LoanOfficer`, `Admin`.

---

## 2. Tech stack (versions as pinned in `pyproject.toml`)

| Tool | Version | Role |
|------|---------|------|
| Python | 3.14 (`.python-version`) | Runtime |
| FastAPI | `0.162.5` | Web framework |
| uvicorn | `0.54.0` | ASGI server |
| SQLAlchemy | `2.0.57` | async ORM (2.0 style) |
| asyncpg | `0.32.0` | PostgreSQL async driver |
| pydantic-settings | `2.16.2` | Environment config |
| alembic | `1.20.1` | Database migrations |
| bcrypt | `4.2.0` | Password hashing |
| python-jose[cryptography] | `3.5.0` | JWT encode/decode |
| python-multipart | `0.0.33` | Form parsing (OAuth2 password flow) |
| pytest | `9.2.0` | Test runner |
| pytest-asyncio | `0.28.1` | Async test support |
| httpx | `0.28.1` | Integration-test HTTP client |
| ruff | `0.17.4` | Lint + format |
| email-validator | `2.3.0` | EmailStr validation for schemas |
| Database | PostgreSQL | (via Docker in Phase 1) |

Dependency management: `pyproject.toml` (PEP 621). Install with:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**Never commit secrets.** `.env` is gitignored; ship only `.env.example`.

---

## 3. Repository structure

```
loanflow-api/
├── AGENTS.md              # this file — keep in sync with code
├── README.md              # user-facing setup/run/migrate/test/endpoint docs
├── pyproject.toml         # metadata, dependencies, ruff config
├── .env.example           # copied to .env locally (gitignored, no secrets)
├── .python-version        # 3.14
├── .gitignore             # Python + venv + ruff + pytest caches
├── Dockerfile             # planned: Phase 1
├── docker-compose.yml     # planned: Phase 1 (API + Postgres)
├── app/                   # application code
│   ├── __init__.py
│   ├── api/               # route layer (FastAPI routers + deps): health, auth, users, loans — Phase 4 done
│   ├── core/              # config (pydantic Settings), security (JWT/password) — Phase 1/3 done
│   ├── models/            # SQLAlchemy 2.0 declarative models — Phase 2 done
│   ├── schemas/           # Pydantic request/response schemas: user, loan — Phase 4 done
│   ├── services/          # business logic (transition rules, password, JWT, loans) — Phase 4 done
│   └── db/                # async engine, async_sessionmaker, session dependency — Phase 1 done
├── tests/                 # pytest suite
│   ├── __init__.py
│   ├── conftest.py        # planned: Phase 5 (fixtures, test DB)
│   ├── unit/              # service-level tests incl. transition rules — planned: Phase 5
│   └── integration/       # endpoint tests against running API — planned: Phase 5
├── alembic/               # migrations (env.py async template) — initialized Phase 2
│   └── versions/
└── .venv/                 # local virtual env (gitignored)
```

Layering rule: `routes → services → DB`. Business logic lives in `services/`, never in routes. Routes only parse input, call services, return responses.

---

## 4. Setup and commands (copy-pasteable)

### Install (local)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then edit .env with local values
```

### Run locally

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run with Docker

```bash
docker compose up --build      # serves API + Postgres; GET /health returns 200
docker compose down
```

### Migrations (planned: Phase 2)

Create a migration:

```bash
source .venv/bin/activate
alembic revision --autogenerate -m "describe change"
```

Upgrade to head:

```bash
alembic upgrade head
```

Downgrade one step:

```bash
alembic downgrade -1
```

### Tests (planned: Phase 5)

```bash
source .venv/bin/activate
pytest
```

Run only unit or integration:

```bash
pytest tests/unit
pytest tests/integration
```

### Lint / format

```bash
source .venv/bin/activate
ruff check .
ruff format .
ruff check --fix .   # auto-fix safe lint issues
```

CI runs `ruff check`, `ruff format --check`, and `pytest` (GitHub Actions, planned: Phase 5).

---

## 5. Architecture rules

1. **Layering**: `routes → services → DB`. Routes handle HTTP only (parse request, call service, return response). Business rules live in `services/`. DB access only via `app/db/` session helpers.
2. **Async-only DB access**: all engine/session operations are async SQLAlchemy 2.0 (`create_async_engine`, `async_sessionmaker`, `AsyncSession`). No sync database calls.
3. **Dependency injection**: session dependency (`get_session`) and current-user dependency (`get_current_user`) are declared in `app/api/deps.py` and injected via FastAPI `Depends`.
4. **Schema vs model separation**: SQLAlchemy models in `app/models/`; Pydantic request/response schemas in `app/schemas/`. Never return ORM objects directly from routes; convert via schemas.
5. **One transaction per status change**: status update + `loan_status_history` insert share the same async session/transaction (planned: Phase 4).

---

## 6. Domain rules

Allowed status transitions (confirmed):

```
submitted -> under_review
under_review -> approved
under_review -> rejected
approved -> (terminal)
rejected  -> (terminal)
```

- No `cancelled` status.
- Transitions are defined explicitly and invalid ones are rejected (400/422).
- Every status change writes one `loan_status_history` row (old status, new status, changed-by user, timestamp) in the same transaction as the status update.
- Status is an enum (Python `str, Enum` + SQLAlchemy `Enum`).

---

## 7. Auth and security rules

- **Role enforcement**: route dependencies require `Applicant` / `LoanOfficer` / `Admin`; unauthorized = `401`, forbidden = `403` (planned: Phase 3).
- **Admin scope** (confirmed): Admin has full access to manage users and roles. LoanOfficer approves/rejects loan applications. Applicant submits applications and views/checks the status of only their own loans.
- **Password hashing**: bcrypt directly (actively maintained), never store plaintext.
- **JWT**: access tokens via `python-jose`, algorithm `HS256` only (explicitly restrict algorithms on decode to prevent key-confusion attacks), short expiry (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- **No secrets in code**: `SECRET_KEY` comes from env only; `.env` is gitignored; `.env.example` has dummy values.
- **No real personal data**: fake data only, in seed scripts and tests.

---

## 8. Coding conventions

- **Naming**: `snake_case` for functions/variables/files, `PascalCase` for classes, `SCREAMING_SNAKE_CASE` for env vars and enum values.
- **Typing**: type hints on all public functions; `from __future__ import annotations` not required (py3.14). Avoid `Any` where a concrete type exists.
- **Schema vs model separation** (see Architecture rules).
- **Error handling**: raise FastAPI `HTTPException` with clear status codes; let unexpected errors surface as 500. Do not swallow exceptions silently.
- **Ruff settings** (in `pyproject.toml`): line-length 88, target `py314`, select `E F I B`, ignore `B008`, double quotes, isort first-party `app`, `tests`. Keep `ruff check` and `ruff format --check` clean.
- **Docstrings**: one-line module/class docstrings; doc public functions.

---

## 9. Testing conventions (planned: Phase 5)

- **Layout**: `tests/unit/` for service-level logic (incl. transition rules); `tests/integration/` for endpoints against the running API; `tests/conftest.py` for shared fixtures.
- **Test DB**: separate test database (`TEST_DATABASE_URL`), not the dev database.
- **Fixtures**: async client, session, seeded users per role.
- **Coverage requirement for any new endpoint**: happy path, 401 (unauthenticated), 403 (wrong role), 404/422 (invalid input/transition), and the history row written in the same transaction.

---

## 10. Git workflow

- Work on a feature branch (e.g. `develop`), **never directly on `main`**.
- Branch naming: `develop` for integration; feature branches like `feature/phase-2-models` from `develop`.
- Commit message style: concise imperative, e.g. `Add pyproject.toml and ruff config`, `Set up app package layout`.
- Keep changes small and commit per logical step with clear messages.
- No direct pushes to `main`. Open a PR into `main` (planned: Phase 6).
- Current branch: `develop`.

---

## 11. Definition of done (checklist for any change)

- [ ] Tests pass (`pytest`)
- [ ] Lint clean (`ruff check .` and `ruff format --check .`)
- [ ] Migration added if models changed (`alembic revision --autogenerate`)
- [ ] README.md updated if behavior changed
- [ ] AGENTS.md updated if commands, structure, or rules changed
- [ ] No secrets or real personal data committed

---

## 12. Do / Don't list

**Do:**
- Use the service layer for business logic; routes stay thin.
- Use async SQLAlchemy 2.0 session dependency for all DB access.
- Restrict JWT algorithms to `HS256` on decode.
- Write a `loan_status_history` row in the same transaction as every status change.
- Keep `.env` out of git; only `.env.example` is committed.
- Pin dependency versions in `pyproject.toml`.

**Don't:**
- Edit applied migrations (create a new migration instead).
- Bypass the service layer by putting logic in routes.
- Store passwords in plaintext.
- Add dependencies without asking first.
- Push directly to `main`.
- Commit `.env`, `.venv/`, or cache directories.

---

## Status by phase

| Phase | Status |
|-------|--------|
| 0 Project setup (.gitignore, pyproject.toml, venv, folder layout, ruff, AGENTS.md) | ✅ done |
| 1 Skeleton (`GET /health`, config, Dockerfile, docker-compose, async engine + session dep) | ✅ done |
| 2 Data model + migrations (users, loan_applications, loan_status_history) | ✅ done |
| 3 Authentication + authorization (register/login, JWT, role deps) | ✅ done |
| 4 Core features (submit/list/view applications, status transitions, history, admin users) | ✅ done |
| 5 Tests + CI (pytest, test DB, GitHub Actions) | planned |
| 6 Polish (seed script, README update, PR into main) | planned |
