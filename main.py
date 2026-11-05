import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router
from middlewares import ErrorMiddleware
logging.basicConfig(level=logging.INFO)
dp=Dispatcher(storage=MemoryStorage()); dp.message.middleware(ErrorMiddleware()); dp.callback_query.middleware(ErrorMiddleware()); dp.include_router(router)

