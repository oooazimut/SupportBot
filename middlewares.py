from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class DataMiddleware(BaseMiddleware):
    def __init__(self, some_data: dict):
        self.some_data = some_data

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        data.update(self.some_data)
        return await handler(event, data)