import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import Command
from database import init_db, async_session, ensure_user
from handlers_admin import router as admin_router

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(admin_router)

@dp.message(Command("start"))
async def cmd_start(message: Message):
    async with async_session() as session:
        await ensure_user(session, message.from_user)
    await message.answer(
        "🛡 <b>Violet Russia | Модератор</b>\n\n"
        "Бот для управления составом и наказаниями.\n"
        "Добавьте меня в чат и выдайте права администратора!\n\n"
        "📜 <b>Команды (в ответ на сообщение):</b>\n"
        "/мут, /размут, /бан, /разбан, /выговор, /профиль"
    )

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
