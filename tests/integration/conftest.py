"""Integration fixtures: PostgreSQL + HTTP client."""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("ANON_SALT", "test-anon-salt")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/15")
os.environ.setdefault(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/learn_english_test",
)
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

from app.core.public_user_id import PUBLIC_ID_INITIAL
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import (  # noqa: F401 — register metadata
    BattleMatchmakingTicket,
    CommonWord,
    User,
    UserPublicIdCounter,
)
from app.models.common_word import CommonWord as CommonWordModel
from app.models.word import DifficultyLevel


@pytest.fixture(scope="session")
def test_database_url() -> str:
    return os.environ["TEST_DATABASE_URL"]


@pytest.fixture(scope="session")
async def engine(test_database_url: str) -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine(test_database_url, echo=False)
    try:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    except OSError as exc:
        await eng.dispose()
        pytest.skip(f"PostgreSQL not available at {test_database_url}: {exc}")
    except Exception as exc:
        await eng.dispose()
        pytest.skip(f"Cannot init test database: {exc}")
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest.fixture(scope="session")
async def seed_catalog(engine: AsyncEngine) -> None:
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        words = [
            ("price", DifficultyLevel.B1),
            ("friend", DifficultyLevel.A1),
            ("water", DifficultyLevel.A1),
            ("school", DifficultyLevel.A2),
            ("achieve", DifficultyLevel.B2),
            ("develop", DifficultyLevel.B1),
            ("important", DifficultyLevel.B2),
            ("quick", DifficultyLevel.A2),
        ]
        for text, level in words:
            session.add(
                CommonWordModel(
                    word_text=text,
                    cefr_level=level,
                    is_everyday_common=True,
                )
            )
        counter = await session.get(UserPublicIdCounter, 1)
        if counter is None:
            session.add(
                UserPublicIdCounter(
                    id=1,
                    next_public_id=PUBLIC_ID_INITIAL,
                )
            )
        await session.commit()


@pytest.fixture
async def db_session(
    engine: AsyncEngine,
    seed_catalog: None,
) -> AsyncIterator[AsyncSession]:
    async with engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    installation_id = f"pytest-{uuid.uuid4().hex}"
    response = await client.post(
        "/api/v1/auth/anonymous",
        json={"installation_id": installation_id},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _register_and_login(client: AsyncClient) -> dict[str, str]:
    suffix = uuid.uuid4().hex[:10]
    email = f"battle_{suffix}@test.example.com"
    username = f"player_{suffix}"
    password = "pytest-secret-1"
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert reg.status_code == 200, reg.text
    login = await client.post(
        "/api/v1/auth/login",
        data={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def registered_auth_headers(client: AsyncClient) -> dict[str, str]:
    return await _register_and_login(client)


@pytest.fixture
async def second_registered_auth_headers(client: AsyncClient) -> dict[str, str]:
    return await _register_and_login(client)


@pytest.fixture
async def second_auth_headers(client: AsyncClient) -> dict[str, str]:
    installation_id = f"pytest-second-{uuid.uuid4().hex}"
    response = await client.post(
        "/api/v1/auth/anonymous",
        json={"installation_id": installation_id},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def learning_words(
    auth_headers: dict[str, str],
    db_session: AsyncSession,
) -> list[int]:
    from jose import jwt

    from app.core.config import settings
    from app.models.word import StudyStatus, Word

    token = auth_headers["Authorization"].split(" ", 1)[1]
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    user_id = int(payload["sub"])

    ids: list[int] = []
    for idx, (text, translation) in enumerate(
        [
            ("apple", "яблуко"),
            ("river", "річка"),
            ("cloud", "хмара"),
            ("garden", "сад"),
            ("planet", "планета"),
        ]
    ):
        word = Word(
            user_id=user_id,
            word_text=f"{text}_{idx}",
            translation=translation,
            study_status=StudyStatus.LEARNING.value,
            difficulty=DifficultyLevel.B1,
        )
        db_session.add(word)
        await db_session.flush()
        ids.append(word.id)
    return ids
