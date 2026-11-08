import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, Integer, Boolean, DateTime

DB_PATH = os.getenv("DB_PATH", "violet.db")
engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}")
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), default="") # <-- ДОБАВИЛ ИМЯ
    role: Mapped[str] = mapped_column(String(32), default="Игрок") # Игрок, Ютубер, Модератор и т.д.
    warns: Mapped[int] = mapped_column(Integer, default=0) # Выговоры
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def ensure_user(session, tg_user):
    user = await session.get(User, tg_user.id)
    if not user:
        # Исправленная строка (теперь first_name, а не второй username)
        user = User(id=tg_user.id, username=tg_user.username, first_name=tg_user.full_name)
        session.add(user)
        await session.commit()
    return user
