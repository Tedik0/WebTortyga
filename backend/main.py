# backend/main.py
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from backend import database          # ← 1. импорт всего модуля
from backend.config import BOT_TOKEN, WEB_URL

# ------------------------------------
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())

# создаём таблицу users сразу при запуске
database.init()
print("USERS DB →", database.DB_PATH.resolve())   # лог для проверки пути
# ------------------------------------

@dp.message(F.text == "/start")
async def cmd_start(msg: types.Message):
    user_id = msg.from_user.id
    database.add_user(user_id)

    url = f"{WEB_URL}?uid={user_id}"  # ← передаём UID
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(
            text="🖥 Открыть веб‑панель",
            web_app=WebAppInfo(url=f"{WEB_URL}?uid={msg.from_user.id}")
        )]]
    )
    await msg.answer("Привет! Открой веб‑панель:", reply_markup=kb)

# ---------- запуск ----------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
