import asyncio
from aiogram import Bot
from config import BOT_TOKEN
async def main():
    import os
    url=os.environ["WEBHOOK_URL"].rstrip("/")+"/api/webhook"
    bot=Bot(BOT_TOKEN); await bot.set_webhook(url); await bot.session.close(); print(url)
if __name__ == "__main__": asyncio.run(main())

