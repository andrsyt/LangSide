# Tests

## Structure (by part)

| Part | Path | Needs DB | What it covers |
|------|------|----------|----------------|
| **1** | `tests/unit/test_english_level.py` | No | CEFR / UI level parsing |
| **1** | `tests/unit/test_battle_*.py` | No | Round answers, ELO, timeouts |
| **1** | `tests/unit/test_today_session_selection.py` | No | Session pick order |
| **2** | `tests/integration/test_api_health_auth.py` | Yes | Health, auth, `/users/me` |
| **2** | `tests/integration/test_users_profile.py` | Yes | `english_level` update |
| **2** | `tests/integration/test_sessions_today.py` | Yes | Today session start/answer/extend |
| **2** | `tests/integration/test_battles_flow.py` | Yes | Battles profile, AI quick duel |
| **3** | `tests/integration/test_matchmaking.py` | Yes | AI join, search/cancel, PvP (registered) |
| **3** | `tests/unit/test_discovery_service.py` | No | Discovery limits + catalog pick |
| **3** | `tests/unit/test_matchmaking_*.py` | No | Messages, voice 501 |
| **4** | `tests/integration/test_words_api.py` | Yes | CRUD words |
| **4** | `tests/integration/test_leaderboard_stats.py` | Yes | Leaderboard + `/stats/home` |

## Setup

```bash
pip install -r requirements-dev.txt

# Create test DB (once)
createdb learn_english_test
# or: docker exec -it learn_english_postgres createdb -U postgres learn_english_test

export TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/learn_english_test
export SECRET_KEY=test-secret
export REDIS_URL=redis://127.0.0.1:6379/15
```

Schema is created via `Base.metadata.create_all` on first test run (no Alembic in tests yet).

## Run

```bash
# Unit only (fast, no Postgres)
pytest tests/unit -v

# Integration (Postgres required)
pytest tests/integration -m integration -v

# All + coverage
pytest tests/ --cov=app --cov-report=term-missing

# Target ~50% coverage (unit ~32% alone; run integration with Postgres)
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=50
```

## Part 5 (optional next)

- `test_friends_api.py` — friend requests
- `test_learning_sessions.py` — structured learning path
- CI: Postgres service container + `pytest tests/ --cov-fail-under=50`

## Notes

- Each integration test runs in a rolled-back DB transaction (isolation).
- `auth_headers` fixture uses anonymous login (unique `installation_id` per test).
- AI battles use `pick_round_count=3` patch for speed.
