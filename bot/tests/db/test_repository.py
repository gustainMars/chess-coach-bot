import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.db.models import Base
from bot.db.repository import get_blunders, get_user, save_blunder, upsert_user
from bot.domain.move_quality import MoveQuality

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"


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
async def test_upsert_user_creates_new(session: AsyncSession):
    await upsert_user(session, telegram_id=1, chesscom_username="alice")
    user = await get_user(session, telegram_id=1)
    assert user is not None
    assert user.chesscom_username == "alice"


@pytest.mark.asyncio
async def test_upsert_user_updates_existing(session: AsyncSession):
    await upsert_user(session, telegram_id=1, chesscom_username="alice")
    await upsert_user(session, telegram_id=1, chesscom_username="alice_new")
    user = await get_user(session, telegram_id=1)
    assert user.chesscom_username == "alice_new"


@pytest.mark.asyncio
async def test_get_user_not_found(session: AsyncSession):
    user = await get_user(session, telegram_id=999)
    assert user is None


@pytest.mark.asyncio
async def test_save_blunder_persists(session: AsyncSession):
    await upsert_user(session, telegram_id=1, chesscom_username="alice")
    blunder = await save_blunder(
        session,
        telegram_id=1,
        opening_eco="C60",
        opening_name="Ruy Lopez",
        fen=STARTING_FEN,
        user_move="Bc4",
        expected_move="Bb5",
        quality=MoveQuality.BLUNDER,
    )
    assert blunder.id is not None
    assert blunder.quality == MoveQuality.BLUNDER.value


@pytest.mark.asyncio
async def test_get_blunders_returns_all(session: AsyncSession):
    await upsert_user(session, telegram_id=1, chesscom_username="alice")
    await save_blunder(session, 1, "C60", "Ruy Lopez", STARTING_FEN, "Bc4", "Bb5", MoveQuality.BLUNDER)
    await save_blunder(session, 1, "D00", "Queens Pawn", STARTING_FEN, "c4", "d4", MoveQuality.MISTAKE)

    blunders = await get_blunders(session, telegram_id=1)
    assert len(blunders) == 2


@pytest.mark.asyncio
async def test_get_blunders_empty_for_unknown_user(session: AsyncSession):
    blunders = await get_blunders(session, telegram_id=999)
    assert blunders == []


@pytest.mark.asyncio
async def test_get_blunders_isolated_per_user(session: AsyncSession):
    await upsert_user(session, telegram_id=1, chesscom_username="alice")
    await upsert_user(session, telegram_id=2, chesscom_username="bob")
    await save_blunder(session, 1, "C60", "Ruy Lopez", STARTING_FEN, "Bc4", "Bb5", MoveQuality.BLUNDER)

    assert len(await get_blunders(session, telegram_id=1)) == 1
    assert len(await get_blunders(session, telegram_id=2)) == 0


@pytest.mark.asyncio
async def test_get_blunders_ordered_by_most_recent(session: AsyncSession):
    await upsert_user(session, telegram_id=1, chesscom_username="alice")
    await save_blunder(session, 1, "C60", "Ruy Lopez", STARTING_FEN, "Bc4", "Bb5", MoveQuality.BLUNDER)
    await save_blunder(session, 1, "D00", "Queens Pawn", STARTING_FEN, "c4", "d4", MoveQuality.MISTAKE)

    blunders = await get_blunders(session, telegram_id=1)
    assert blunders[0].opening_eco == "D00"
