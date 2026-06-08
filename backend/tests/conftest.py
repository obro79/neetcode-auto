from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import session as db_session
from app.database.session import get_session
from app.enums import Difficulty, ReviewStage
from app.main import app
from app.models.base import Base
from app.models.problem import Problem
from app.models.user_progress import UserProgress


@pytest.fixture(autouse=True)
def clear_config_caches():
    from app.core.config import get_settings
    from app.core.srs_config import get_srs_config

    get_settings.cache_clear()
    get_srs_config.cache_clear()
    yield
    get_settings.cache_clear()
    get_srs_config.cache_clear()


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session(test_engine) -> AsyncIterator[AsyncSession]:
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def seeded_session(session: AsyncSession) -> AsyncSession:
    problem = Problem(
        slug="two-integer-sum",
        title="Two Sum",
        pattern="Arrays & Hashing",
        difficulty=Difficulty.EASY,
        leetcode_url="https://leetcode.com/problems/two-sum/",
        neetcode_url="https://neetcode.io/problems/two-integer-sum",
        sort_order=1,
    )
    session.add(problem)
    await session.flush()
    session.add(
        UserProgress(
            problem_id=problem.id,
            solved=False,
            review_stage=ReviewStage.NEW,
        )
    )
    await session.commit()
    return session


@pytest_asyncio.fixture
async def client(test_engine, monkeypatch) -> AsyncIterator[AsyncClient]:
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    monkeypatch.setattr(db_session, "AsyncSessionLocal", session_factory)
    monkeypatch.setenv("API_KEY", "test-api-key")

    from app.core.config import get_settings

    get_settings.cache_clear()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client

    app.dependency_overrides.clear()
    get_settings.cache_clear()


@pytest.fixture
def api_headers() -> dict[str, str]:
    return {"X-API-Key": "test-api-key"}
