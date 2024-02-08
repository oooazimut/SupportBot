import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.exceptions import UnknownIntent
from redis.asyncio.client import Redis

import config
from db.db_models import SqLiteDataBase
from db.service import TaskService, EmployeeService
from dialogs import customer
from handlers.error_handlers import ui_error_handler
from routers import start_router, finish_router

_logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

db = SqLiteDataBase('Support.db')
task_service = TaskService(db)
empl_service = EmployeeService(db)


async def main():
    bot = Bot(config.TOKEN)
    storage = RedisStorage(Redis(), key_builder=DefaultKeyBuilder(with_destiny=True))
    dp = Dispatcher(storage=storage)
    dp.include_routers(start_router.router, customer.main_dialog, customer.create_task_dialog,
                       finish_router.router)
    setup_dialogs(dp)
    dp.errors.register(ui_error_handler, ExceptionTypeFilter(UnknownIntent))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
