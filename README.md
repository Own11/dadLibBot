# Book Reader Telegram Bot

Бот использует Python 3.11+, aiogram 3, FastAPI, asyncpg, Neon Postgres и edge-tts.

1. Создайте проект Neon, выполните `schema.sql`, установите `python -m venv .venv && pip install -r requirements.txt` и скопируйте `.env.example` в `.env`.
2. Для локальной отладки webhook-запуск: `uvicorn api.index:app --reload`. Проверка: `GET /api/health`. Для ручной обработки очереди: `curl -H "Authorization: Bearer $CRON_SECRET" http://localhost:8000/api/cron`.
3. Для polling локально можно добавить небольшой скрипт: `asyncio.run(dp.start_polling(Bot(BOT_TOKEN)))`; на Vercel polling не используется.
4. Задайте переменные Vercel, задеплойте проект и выполните `WEBHOOK_URL=https://project.vercel.app python set_webhook.py`.

Поиск хранится в FSM-памяти процесса, а callback содержит только префикс и страницу. В production для нескольких инстансов замените MemoryStorage на Redis или другую внешнюю FSM storage. `user_id` всегда берётся из Telegram update. SQL использует LIMIT/OFFSET и COUNT. Соединение с Neon создаётся и закрывается на каждый запрос, чтобы не держать пул в serverless; учитывайте лимит соединений Neon. Cron атомарно блокирует один pending job через `FOR UPDATE SKIP LOCKED`, синтезирует один чанк до 900 символов и продолжает его на следующем вызове.

