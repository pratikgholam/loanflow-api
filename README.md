# Loan Flow API

A loan application REST API where applicants submit loans and loan officers review them, with every status change recorded in history. Built with FastAPI, async SQLAlchemy 2.0 and PostgreSQL. Uses JWT authentication with Applicant, LoanOfficer and Admin roles. Fake data only.

## Setup (local)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp -n .env.example .env   # then edit .env with local values
```

## Run locally

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run with Docker

```bash
docker compose up --build      # serves API + Postgres; GET /health returns 200
docker compose down
```

## Migrations

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

## Tests

```bash
source .venv/bin/activate
pytest
```

Run only unit or integration:

```bash
pytest tests/unit
pytest tests/integration
```

## Lint / format

```bash
source .venv/bin/activate
ruff check .
ruff format .
ruff check --fix .   # auto-fix safe lint issues
```

## Security

- **Rate limiting**: `POST /auth/login` (5 requests/minute) and `POST /auth/register` (3 requests/minute) are rate limited per client IP. Exceeding the limit returns `429 Too Many Requests`.
- **No secrets in code**: `SECRET_KEY` comes from env only; `.env` is gitignored; `.env.example` has dummy values.
- **Fake data only**: seed scripts and tests use fake data. No real personal data anywhere.

## Seed script (development only)

```bash
source .venv/bin/activate
SEED_LOAN_OFFICER_PASSWORD=officer-secret-change-me \
SEED_APPLICANT_PASSWORD=applicant-secret-change-me \
python -m app.seed
```

Creates `admin`, `loan_officer`, and `applicant` users if they don't exist. Refuses to run unless `APP_ENV=development`. The admin password comes from `ADMIN_PASSWORD` (env); the other two passwords must be supplied via the vars above.

## Endpoints

### Auth
- `POST /auth/register` — register an applicant account
- `POST /auth/login` — OAuth2 password flow, returns a JWT

### Users (admin only)
- `GET /users` — list all users
- `GET /users/{user_id}` — get a user
- `PATCH /users/{user_id}` — update a user's role/is_active

### Loan applications
- `POST /applications` — submit a new application (applicant only)
- `GET /applications` — list all (loan officer) or own (applicant); filter `?status=`
- `GET /applications/{application_id}` — view an application (owner or officer/admin)
- `PATCH /applications/{application_id}/status` — approve or reject (loan officer only)

Status transitions: `submitted → under_review → {approved, rejected}`; both terminal. Every status change writes a `loan_status_history` row in the same transaction.

Roles: `Applicant`, `LoanOfficer`, `Admin`.
