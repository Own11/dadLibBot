import asyncio
from aiogram import Bot
from config import BOT_TOKEN
from main import dp

async def main():
    bot = Bot(BOT_TOKEN)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
