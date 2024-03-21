import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.exceptions import UnknownIntent
from redis.asyncio.client import Redis
from handlers import task
import config
from dialogs import customers, workers, operators, task
from handlers.errors import ui_error_handler
from routers import start_router, finish_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler

_logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


async def main():
    bot = Bot(config.TOKEN)
    storage = RedisStorage(Redis(), key_builder=DefaultKeyBuilder(with_destiny=True, with_bot_id=True))
    dp = Dispatcher(storage=storage)
    dp.include_router(start_router.router)
    dp.include_routers(customers.main_dialog)
    dp.include_router(task.create_task_dialog)
    dp.include_routers(workers.main_dialog, workers.task_dialog)
    dp.include_routers(
        operators.main_dialog,
        operators.task_dialog,
        operators.worker_dialog,
        operators.edit_task_dialog,
        operators.worker_send_dialog
    )
    dp.include_router(finish_router.router)

    sheduler=AsyncIOScheduler()
    sheduler.start()
    sheduler.add_job(
        task.reminders_task_to_worker,
        'interval',
        seconds=3600,
        id='send_task_to_worker',
        kwargs={'bot': bot, 'sheduler': sheduler},
    )
    sheduler.add_job(
        task.reminders_task_to_morning,
        'crone',
        day_of_week='mon-fri',
        hour=9
    )

    setup_dialogs(dp)
    dp.errors.register(ui_error_handler, ExceptionTypeFilter(UnknownIntent))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
