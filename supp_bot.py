import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.exceptions import UnknownIntent
from redis.asyncio.client import Redis

import config
<<<<<<< HEAD
from dialogs import customers, workers, operators
=======
from dialogs import customers, workers, operators, new_task
>>>>>>> 13e42f81ac98710c6bf99bd0aebb7985326d15a8
from handlers.error_handlers import ui_error_handler
from routers import start_router, finish_router

_logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


async def main():
    bot = Bot(config.TOKEN)
    storage = RedisStorage(Redis(), key_builder=DefaultKeyBuilder(with_destiny=True, with_bot_id=True))
    dp = Dispatcher(storage=storage)
<<<<<<< HEAD

    dp.include_router(start_router.router)
    dp.include_routers(customers.main_dialog, customers.create_task_dialog, customers.task_dialog)
    dp.include_routers(workers.main_dialog, workers.task_dialog)
    dp.include_routers(operators.main_dialog, operators.worker_dialog,
                       operators.add_worker_dialog, operators.task_dialog)
=======
    dp.include_router(start_router.router)
    dp.include_routers(customers.main_dialog)
    dp.include_router(new_task.create_task_dialog)
    dp.include_routers(workers.main_dialog, workers.task_dialog)
    dp.include_routers(
        operators.main_dialog,
        operators.task_dialog,
        operators.worker_dialog,
        operators.edit_task_dialog,
        operators.worker_send_dialog
    )
>>>>>>> 13e42f81ac98710c6bf99bd0aebb7985326d15a8
    dp.include_router(finish_router.router)

    setup_dialogs(dp)
    dp.errors.register(ui_error_handler, ExceptionTypeFilter(UnknownIntent))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
