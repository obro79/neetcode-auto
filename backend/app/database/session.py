import ssl
from collections.abc import AsyncIterator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


def _asyncpg_connect_args(database_url: str) -> tuple[str, dict]:
    parsed = urlparse(database_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    connect_args: dict = {}

    sslmode = query.pop("sslmode", None)
    query.pop("channel_binding", None)

    if sslmode in {"require", "verify-ca", "verify-full"}:
        connect_args["ssl"] = ssl.create_default_context()

    clean_query = urlencode(query)
    clean_url = urlunparse(parsed._replace(query=clean_query))
    return clean_url, connect_args


settings = get_settings()
database_url, connect_args = _asyncpg_connect_args(settings.database_url)
engine = create_async_engine(
    database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


get_session = get_db_session
