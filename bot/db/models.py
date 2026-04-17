from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    chesscom_username: Mapped[str] = mapped_column(String, nullable=False)

    blunders: Mapped[list["Blunder"]] = relationship("Blunder", back_populates="user", cascade="all, delete-orphan")


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

    user: Mapped["User"] = relationship("User", back_populates="blunders")
