from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.db.models import Base
from bot.db.repository import get_cached_explorer_moves, save_cached_explorer_moves

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
FEN = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
MOVES = ["e7e5", "c7c5", "e7e6"]


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_cached_returns_none_when_missing(session):
    result = await get_cached_explorer_moves(session, FEN)
    assert result is None


@pytest.mark.asyncio
async def test_save_and_get_returns_moves(session):
    await save_cached_explorer_moves(session, FEN, MOVES)
    result = await get_cached_explorer_moves(session, FEN)
    assert result == MOVES


@pytest.mark.asyncio
async def test_save_upserts_existing_entry(session):
    await save_cached_explorer_moves(session, FEN, ["e7e5"])
    updated = ["d7d5", "c7c5"]
    await save_cached_explorer_moves(session, FEN, updated)
    result = await get_cached_explorer_moves(session, FEN)
    assert result == updated


@pytest.mark.asyncio
async def test_get_cached_returns_none_when_expired(session):
    await save_cached_explorer_moves(session, FEN, MOVES)

    # Simulate the cached_at being 31 days in the past
    stale_time = datetime.now(timezone.utc) - timedelta(days=31)
    with patch("bot.db.repository.datetime") as mock_dt:
        mock_dt.now.return_value = stale_time
        # Re-save with the mocked (old) timestamp
        await save_cached_explorer_moves(session, FEN, MOVES)

    result = await get_cached_explorer_moves(session, FEN)
    assert result is None


@pytest.mark.asyncio
async def test_get_cached_returns_moves_within_ttl(session):
    await save_cached_explorer_moves(session, FEN, MOVES)

    # 29 days old — still within 30-day TTL
    recent_time = datetime.now(timezone.utc) - timedelta(days=29)
    with patch("bot.db.repository.datetime") as mock_dt:
        mock_dt.now.return_value = recent_time
        await save_cached_explorer_moves(session, FEN, MOVES)

    result = await get_cached_explorer_moves(session, FEN)
    assert result == MOVES


@pytest.mark.asyncio
async def test_save_empty_list(session):
    await save_cached_explorer_moves(session, FEN, [])
    result = await get_cached_explorer_moves(session, FEN)
    assert result == []
