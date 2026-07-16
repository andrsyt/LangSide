# EnglishApp (Learn English API)

Backend for a vocabulary learning product: spaced repetition, guided training quests, social battles, and iOS subscription sync via RevenueCat.

Companion mobile client talks to this API; this repository is the **FastAPI** service.

## Stack

- Python 3.12+
- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (async) + Alembic
- PostgreSQL, Redis, Celery
- Docker / docker-compose

## Architecture

```text
API (FastAPI routers)
  → Services (use cases)
    → Repositories (SQLAlchemy)
  → Domain helpers (pure rules / mapping)
```

Dependency injection lives in `app/api/deps.py`. Application errors use a typed exception hierarchy under `app/core/exceptions/` with unified HTTP handlers.

See [docs/architecture.md](docs/architecture.md) for a short layer overview.

## Features

- Auth: register / login, JWT access + refresh tokens, anonymous device login
- Vocabulary: CRUD, AI-assisted analysis, translation sync on preferred-language change
- Practice: today sessions, mixed learning sessions, spaced-repetition reviews
- Training quests: semantic anchor, double recall, anti-confusion, associations
- Social: friends, matchmaking, ranked / AI battles, leaderboards
- Billing: free/premium limits, RevenueCat webhook + restore

## Quick start

### Prerequisites

- Python 3.12+
- Docker (Postgres + Redis) **or** local Postgres/Redis matching `.env.example`

### Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements-dev.txt
cp .env.example .env
# Edit SECRET_KEY, ANON_SALT, DATABASE_URL, REDIS_URL
```

### Infrastructure

```bash
docker compose up -d postgres redis
alembic upgrade head
```

### Run API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: `GET /health`
- OpenAPI: `http://localhost:8000/docs`

Production-style stack: `docker compose -f docker-compose.prod.yml up -d --build`.

## Tests

Unit tests do not require a running Postgres instance:

```bash
pytest tests/unit -q
```

Integration tests (optional) need `TEST_DATABASE_URL` and are marked `integration`.

Lint (dev):

```bash
ruff check app tests
```

## Project layout

```text
app/
  api/           # HTTP routers + DI
  core/          # config, security, exceptions
  domain/        # pure domain rules
  helpers/       # access guards, mappers, utilities
  models/        # SQLAlchemy models
  repository/    # data access
  schemas/       # Pydantic schemas
  services/      # application use cases (by domain package)
  tasks/         # Celery tasks
alembic/         # migrations
tests/           # unit (+ optional integration)
docs/            # public documentation
docker/          # container helpers
```

## Configuration

Copy [`.env.example`](.env.example). Never commit `.env`. Required production secrets include `SECRET_KEY`, `ANON_SALT`, database credentials, and RevenueCat keys when billing is enabled.

## License

MIT — see [LICENSE](LICENSE).
