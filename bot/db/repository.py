from datetime import datetime

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert

from bot.db.models import Blunder, User, UserOpeningStat
from bot.domain.move_quality import MoveQuality


async def upsert_user(
    session: AsyncSession, telegram_id: int, chesscom_username: str
) -> None:
    stmt = (
        insert(User)
        .values(telegram_id=telegram_id, chesscom_username=chesscom_username)
        .on_conflict_do_update(
            index_elements=["telegram_id"],
            set_={"chesscom_username": chesscom_username},
        )
    )
    await session.execute(stmt)
    await session.commit()


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def upsert_opening_stat(
    session: AsyncSession,
    chesscom_username: str,
    eco: str,
    color: str,
    month: int,
    year: int,
    rating: int | None,
    total: int,
    wins: int,
    losses: int,
    draws: int,
) -> None:
    stmt = (
        insert(UserOpeningStat)
        .values(
            chesscom_username=chesscom_username,
            eco=eco,
            color=color,
            month=month,
            year=year,
            rating=rating,
            total=total,
            wins=wins,
            losses=losses,
            draws=draws,
        )
        # rating is intentionally excluded — only written on the first INSERT of the month
        .on_conflict_do_update(
            index_elements=["chesscom_username", "eco", "color", "month", "year"],
            set_={"total": total, "wins": wins, "losses": losses, "draws": draws},
        )
    )
    await session.execute(stmt)
    await session.commit()


async def get_previous_rating(
    session: AsyncSession, chesscom_username: str, current_month: int, current_year: int
) -> int | None:
    result = await session.execute(
        select(UserOpeningStat.rating)
        .where(
            UserOpeningStat.chesscom_username == chesscom_username,
            UserOpeningStat.rating.is_not(None),
            (UserOpeningStat.year * 12 + UserOpeningStat.month)
            < (current_year * 12 + current_month),
        )
        .order_by((UserOpeningStat.year * 12 + UserOpeningStat.month).desc())
        .limit(1)
    )
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


async def get_blunder_by_id(session: AsyncSession, blunder_id: int) -> Blunder | None:
    result = await session.execute(select(Blunder).where(Blunder.id == blunder_id))
    return result.scalar_one_or_none()


async def mark_blunder_reviewed(session: AsyncSession, blunder_id: int) -> None:
    await session.execute(
        update(Blunder)
        .where(Blunder.id == blunder_id)
        .values(reviewed_at=datetime.utcnow())
    )
    await session.commit()


async def reset_all_reviews(session: AsyncSession, telegram_id: int) -> None:
    await session.execute(
        update(Blunder)
        .where(Blunder.telegram_id == telegram_id)
        .values(reviewed_at=None)
    )
    await session.commit()


async def get_next_unreviewed_blunder(
    session: AsyncSession, telegram_id: int
) -> tuple[Blunder | None, bool]:
    result = await session.execute(
        select(Blunder)
        .where(Blunder.telegram_id == telegram_id, Blunder.reviewed_at.is_(None))
        .order_by(Blunder.created_at.asc())
        .limit(1)
    )
    blunder = result.scalar_one_or_none()
    if blunder is not None:
        return blunder, False

    count_result = await session.execute(
        select(func.count()).where(Blunder.telegram_id == telegram_id)
    )
    count = count_result.scalar_one()
    if count == 0:
        return None, False

    await reset_all_reviews(session, telegram_id)
    result = await session.execute(
        select(Blunder)
        .where(Blunder.telegram_id == telegram_id)
        .order_by(Blunder.created_at.asc())
        .limit(1)
    )
    return result.scalar_one_or_none(), True
