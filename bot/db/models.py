from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    chesscom_username: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    blunders: Mapped[list["Blunder"]] = relationship("Blunder", back_populates="user", cascade="all, delete-orphan")
    opening_stats: Mapped[list["UserOpeningStat"]] = relationship("UserOpeningStat", back_populates="user", cascade="all, delete-orphan")


class Blunder(Base):
    __tablename__ = "blunders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    opening_eco: Mapped[str] = mapped_column(String, nullable=False)
    opening_name: Mapped[str] = mapped_column(String, nullable=False)
    fen: Mapped[str] = mapped_column(String, nullable=False)
    user_move: Mapped[str] = mapped_column(String, nullable=False)
    expected_move: Mapped[str] = mapped_column(String, nullable=False)
    quality: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)

    user: Mapped["User"] = relationship("User", back_populates="blunders")


class UserOpeningStat(Base):
    __tablename__ = "user_opening_stats"
    __table_args__ = (
        UniqueConstraint("chesscom_username", "eco", "color", "month", "year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chesscom_username: Mapped[str] = mapped_column(String, ForeignKey("users.chesscom_username"), nullable=False)
    eco: Mapped[str] = mapped_column(String, nullable=False)
    color: Mapped[str] = mapped_column(String, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    losses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    draws: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["User"] = relationship("User", back_populates="opening_stats")
