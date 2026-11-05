import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
CRON_SECRET = os.getenv("CRON_SECRET", "")
TTS_VOICE = os.getenv("TTS_VOICE", "ru-RU-DmitryNeural")
TTS_RATE = os.getenv("TTS_RATE", "+0%")
TTS_VOLUME = os.getenv("TTS_VOLUME", "+0%")
PAGE_SIZE = 5

