import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.exceptions import UnknownIntent
from redis.asyncio.client import Redis

import config
from dialogs import customers, workers
from handlers.error_handlers import ui_error_handler
from routers import start_router, finish_router

_logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


async def main():
    bot = Bot(config.TOKEN)
    storage = RedisStorage(Redis(), key_builder=DefaultKeyBuilder(with_destiny=True))
    dp = Dispatcher(storage=storage)
    dp.include_routers(start_router.router, customers.main_dialog, customers.create_task_dialog,
                       finish_router.router, workers.main_dialog)
    setup_dialogs(dp)
    dp.errors.register(ui_error_handler, ExceptionTypeFilter(UnknownIntent))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
