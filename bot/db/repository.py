from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert

from bot.db.models import Blunder, User
from bot.domain.move_quality import MoveQuality


async def upsert_user(session: AsyncSession, telegram_id: int, chesscom_username: str) -> None:
    stmt = (
        insert(User)
        .values(telegram_id=telegram_id, chesscom_username=chesscom_username)
        .on_conflict_do_update(index_elements=["telegram_id"], set_={"chesscom_username": chesscom_username})
    )
    await session.execute(stmt)
    await session.commit()


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def save_blunder(
    session: AsyncSession,
    telegram_id: int,
    opening_eco: str,
    opening_name: str,
    fen: str,
    user_move: str,
    expected_move: str,
    quality: MoveQuality,
) -> Blunder:
    blunder = Blunder(
        telegram_id=telegram_id,
        opening_eco=opening_eco,
        opening_name=opening_name,
        fen=fen,
        user_move=user_move,
        expected_move=expected_move,
        quality=quality.value,
    )
    session.add(blunder)
    await session.commit()
    await session.refresh(blunder)
    return blunder


async def get_blunders(session: AsyncSession, telegram_id: int) -> list[Blunder]:
    result = await session.execute(
        select(Blunder)
        .where(Blunder.telegram_id == telegram_id)
        .order_by(Blunder.created_at.desc())
    )
    return list(result.scalars().all())
