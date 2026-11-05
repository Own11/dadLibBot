import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi import FastAPI, Request
from aiogram import Bot
from config import BOT_TOKEN
from main import dp
app=FastAPI()
@app.get("/api/health")
async def health(): return {"status":"ok"}
@app.post("/api/webhook")
async def webhook(request: Request):
    bot=Bot(BOT_TOKEN)
    try: return await dp.feed_raw_update(bot, await request.json())
    finally: await bot.session.close()

