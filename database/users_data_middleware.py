from typing import Callable, Awaitable, Dict, Any
from aiogram.types import TelegramObject
from aiogram import Bot, Dispatcher, BaseMiddleware


class UsersDataMiddleware(BaseMiddleware):
    def __init__(self, users_data):
        self.users_data = users_data

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        data["users_data"] = self.users_data
        return await handler(event, data)
