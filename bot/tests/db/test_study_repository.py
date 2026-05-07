import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.db.models import Base
from bot.db.repository import (
    get_blunder_by_id,
    get_next_unreviewed_blunder,
    mark_blunder_reviewed,
    reset_all_reviews,
    save_blunder,
    upsert_user,
)
from bot.domain.move_quality import MoveQuality

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
FEN = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


async def _make_user(session, telegram_id=1, username="alice"):
    await upsert_user(session, telegram_id=telegram_id, chesscom_username=username)


async def _make_blunder(session, telegram_id=1, eco="C60", name="Ruy Lopez"):
    return await save_blunder(
        session,
        telegram_id=telegram_id,
        opening_eco=eco,
        opening_name=name,
        fen=FEN,
        user_move="Bc4",
        expected_move="Bb5",
        quality=MoveQuality.BLUNDER,
    )


@pytest.mark.asyncio
async def test_get_next_unreviewed_returns_none_when_no_blunders(session: AsyncSession):
    await _make_user(session)
    blunder, reset = await get_next_unreviewed_blunder(session, telegram_id=1)
    assert blunder is None
    assert reset is False


@pytest.mark.asyncio
async def test_get_next_unreviewed_returns_oldest_first(session: AsyncSession):
    await _make_user(session)
    first = await _make_blunder(session, eco="C60", name="Ruy Lopez")
    second = await _make_blunder(session, eco="D00", name="Queens Pawn")

    blunder, reset = await get_next_unreviewed_blunder(session, telegram_id=1)
    assert blunder is not None
    assert blunder.id == first.id
    assert reset is False


@pytest.mark.asyncio
async def test_mark_blunder_reviewed_sets_timestamp(session: AsyncSession):
    await _make_user(session)
    b = await _make_blunder(session)

    await mark_blunder_reviewed(session, b.id)
    fetched = await get_blunder_by_id(session, b.id)
    assert fetched.reviewed_at is not None


@pytest.mark.asyncio
async def test_get_next_unreviewed_skips_reviewed(session: AsyncSession):
    await _make_user(session)
    first = await _make_blunder(session, eco="C60", name="Ruy Lopez")
    second = await _make_blunder(session, eco="D00", name="Queens Pawn")

    await mark_blunder_reviewed(session, first.id)

    blunder, reset = await get_next_unreviewed_blunder(session, telegram_id=1)
    assert blunder is not None
    assert blunder.id == second.id
    assert reset is False


@pytest.mark.asyncio
async def test_auto_reset_when_all_reviewed(session: AsyncSession):
    await _make_user(session)
    b1 = await _make_blunder(session, eco="C60", name="Ruy Lopez")
    b2 = await _make_blunder(session, eco="D00", name="Queens Pawn")

    await mark_blunder_reviewed(session, b1.id)
    await mark_blunder_reviewed(session, b2.id)

    blunder, reset = await get_next_unreviewed_blunder(session, telegram_id=1)
    assert reset is True
    assert blunder is not None
    # After reset the oldest blunder is returned again
    assert blunder.id == b1.id


@pytest.mark.asyncio
async def test_reset_all_reviews_clears_timestamps(session: AsyncSession):
    await _make_user(session)
    b = await _make_blunder(session)
    await mark_blunder_reviewed(session, b.id)

    await reset_all_reviews(session, telegram_id=1)
    fetched = await get_blunder_by_id(session, b.id)
    assert fetched.reviewed_at is None


@pytest.mark.asyncio
async def test_get_next_unreviewed_isolated_per_user(session: AsyncSession):
    await _make_user(session, telegram_id=1, username="alice")
    await _make_user(session, telegram_id=2, username="bob")

    b = await _make_blunder(session, telegram_id=1)
    await mark_blunder_reviewed(session, b.id)

    # User 1 has all blunders reviewed → should auto-reset for user 1
    blunder1, reset1 = await get_next_unreviewed_blunder(session, telegram_id=1)
    assert reset1 is True

    # User 2 has no blunders → returns None, no reset
    blunder2, reset2 = await get_next_unreviewed_blunder(session, telegram_id=2)
    assert blunder2 is None
    assert reset2 is False


@pytest.mark.asyncio
async def test_get_blunder_by_id_returns_correct(session: AsyncSession):
    await _make_user(session)
    b = await _make_blunder(session)

    fetched = await get_blunder_by_id(session, b.id)
    assert fetched is not None
    assert fetched.id == b.id
    assert fetched.opening_eco == "C60"


@pytest.mark.asyncio
async def test_get_blunder_by_id_returns_none_for_missing(session: AsyncSession):
    fetched = await get_blunder_by_id(session, blunder_id=99999)
    assert fetched is None
