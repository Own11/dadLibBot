# Book Reader Telegram Bot

Бот использует Python 3.11+, aiogram 3, FastAPI, asyncpg, Neon Postgres и edge-tts.

На Vercel Hobby cron в `vercel.json` запускается один раз в сутки (`0 3 * * *`). Для быстрой обработки очереди озвучки вызывайте `/api/cron` внешним cron-сервисом чаще, передавая `Authorization: Bearer CRON_SECRET`, либо используйте Vercel Pro.

## Расширенные возможности

- Книги с текстом читаются постранично. Каждое открытие сохраняет `last_page` и `last_opened_at`, поэтому кнопка чтения продолжает с последнего места.
- `book_pages` и `book_chapters` позволяют хранить страницы и главы отдельно. Администратор при добавлении текста автоматически создаёт страницы.
- TTS обрабатывает одну страницу очереди за cron-вызов, сохраняет каждый Telegram `file_id`, отправляет чанки по порядку и повторяет ошибки до `TTS_MAX_ATTEMPTS` раз.
- Администратор задаётся через `ADMIN_IDS` и может использовать `/admin_books`, `/admin_add | Название | Автор | Полный текст`, `/admin_delete <id>`.

1. Создайте проект Neon. Для существующей базы повторно выполните `schema.sql`: он содержит безопасные `CREATE IF NOT EXISTS` и `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. Затем установите `python -m venv .venv && pip install -r requirements.txt` и скопируйте `.env.example` в `.env`.
2. Для локальной отладки webhook-запуск: `uvicorn api.index:app --reload`. Проверка: `GET /api/health`. Для ручной обработки очереди: `curl -H "Authorization: Bearer $CRON_SECRET" http://localhost:8000/api/cron`.
3. Для polling локально запустите `python run_polling.py`; на Vercel polling не используется.
4. Задайте переменные Vercel, задеплойте проект и выполните `WEBHOOK_URL=https://project.vercel.app python set_webhook.py`.

Поиск хранится в FSM-памяти процесса, а callback содержит только префикс и страницу. В production для нескольких инстансов замените MemoryStorage на Redis или другую внешнюю FSM storage. `user_id` всегда берётся из Telegram update. SQL использует LIMIT/OFFSET и COUNT. Соединение с Neon создаётся и закрывается на каждый запрос, чтобы не держать пул в serverless; учитывайте лимит соединений Neon. Cron атомарно блокирует один pending job через `FOR UPDATE SKIP LOCKED`, синтезирует один чанк до 900 символов и продолжает его на следующем вызове.

