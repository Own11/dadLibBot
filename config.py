import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
CRON_SECRET = os.getenv("CRON_SECRET", "")
TTS_VOICE = os.getenv("TTS_VOICE", "ru-RU-DmitryNeural")
TTS_RATE = os.getenv("TTS_RATE", "+0%")
TTS_VOLUME = os.getenv("TTS_VOLUME", "+0%")
PAGE_SIZE = 5
BOOK_PAGE_SIZE = 3500
TTS_MAX_ATTEMPTS = int(os.getenv("TTS_MAX_ATTEMPTS", "3"))
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}

