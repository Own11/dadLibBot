import logging
from aiogram import BaseMiddleware
from typing import Any, Awaitable, Callable
class ErrorMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable, event: Any, data: dict) -> Any:
        try: return await handler(event, data)
        except Exception:
            logging.exception("Ошибка обработки Telegram update")
            if hasattr(event, "answer"): await event.answer("Произошла ошибка. Попробуйте ещё раз.")

