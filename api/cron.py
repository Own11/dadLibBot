import sys, os, tempfile, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot
from config import BOT_TOKEN, CRON_SECRET
from db import connection
from tts import synthesize
app=FastAPI(); log=logging.getLogger(__name__)
@app.get("/api/cron")
@app.post("/api/cron")
async def cron(request: Request):
    if request.headers.get("authorization") != f"Bearer {CRON_SECRET}": raise HTTPException(401,"Unauthorized")
    async with connection() as c:
        async with c.transaction():
            row=await c.fetchrow("SELECT j.id,j.user_id,j.book_id,j.chunk_index,ch.text_content FROM audio_jobs j JOIN audio_chunks ch ON ch.job_id=j.id AND ch.chunk_index=j.chunk_index WHERE j.status='pending' ORDER BY j.created_at FOR UPDATE OF j SKIP LOCKED LIMIT 1")
            if not row: return {"status":"idle"}
            await c.execute("UPDATE audio_jobs SET status='processing',updated_at=NOW() WHERE id=$1",row['id'])
    bot=Bot(BOT_TOKEN); path=os.path.join(tempfile.gettempdir(),f"audio-{row['id']}-{row['chunk_index']}.mp3")
    try:
        await synthesize(row['text_content'],path); msg=await bot.send_audio(row['user_id'],__import__('aiogram').types.FSInputFile(path))
        async with connection() as c:
            await c.execute("INSERT INTO audio_chunks(job_id,chunk_index,telegram_file_id) VALUES($1,$2,$3) ON CONFLICT(job_id,chunk_index) DO UPDATE SET telegram_file_id=$3",row['id'],row['chunk_index'],msg.audio.file_id)
            done=row['chunk_index']+1 >= await c.fetchval("SELECT total_chunks FROM audio_jobs WHERE id=$1",row['id'])
            await c.execute("UPDATE audio_jobs SET chunk_index=chunk_index+1,status=$2,updated_at=NOW() WHERE id=$1",row['id'],'done' if done else 'pending')
        if done: await bot.send_message(row['user_id'],'Озвучка книги завершена.')
        return {"status":"done","job_id":row['id']}
    except Exception as exc:
        log.exception("Ошибка TTS");
        async with connection() as c: await c.execute("UPDATE audio_jobs SET status='failed',error=$2,updated_at=NOW() WHERE id=$1",row['id'],str(exc))
        await bot.send_message(row['user_id'],'Не удалось озвучить книгу.'); return {"status":"failed"}
    finally:
        await bot.session.close()
        if os.path.exists(path): os.unlink(path)

