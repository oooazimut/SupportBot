import asyncio
import logging

from aiogram import Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import ErrorEvent
from aiogram_dialog import DialogManager, StartMode, setup_dialogs
from aiogram_dialog.api.exceptions import UnknownIntent
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis.asyncio.client import Redis

import config
import jobs
import middlewares
from bot import MyBot
from routers import finish_router, start_router
from db import empl_service

_logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

async def ui_error_handler(event: ErrorEvent, dialog_manager: DialogManager):
    userid = dialog_manager.middleware_data['event_from_user'].id
    user = empl_service.get_employee(userid=userid)
    if user:
        position = user['position']
    else:
        position = 'customer'
    await dialog_manager.start(state=config.START_STATES[position], mode=StartMode.RESET_STACK)


async def main():
    bot = MyBot(config.TOKEN, parse_mode=ParseMode.HTML).get_instance()
    storage = RedisStorage(
        Redis(), key_builder=DefaultKeyBuilder(with_destiny=True, with_bot_id=True)
    )
    dp = Dispatcher(storage=storage)
    dp.include_router(start_router.router)
    dp.include_routers(customers.main_dialog)
    dp.include_routers(tasks.create_task_dialog)
    dp.include_routers(workers.main_dialog, workers.task_dialog)
    dp.include_routers(
        operators.main_dialog,
        operators.task_dialog,
        operators.DelayDialog,
        operators.worker_dialog,
    )
    dp.include_router(finish_router.router)
    scheduler = AsyncIOScheduler()
    scheduler.add_jobstore(
        "redis", jobs_key="example.jobs", run_times_key="example.run_times"
    )
    scheduler.start()
    scheduler.add_job(
        func=jobs.reminders_task_to_worker,
        trigger="cron",
        hour="9-16",
        id="send_task_to_worker",
        replace_existing=True,
    )
    scheduler.add_job(
        jobs.reminders_task_to_morning,
        trigger="cron",
        hour=9,
        id="morning_report",
        replace_existing=True,
    )
    setup_dialogs(dp)
    dp.update.outer_middleware(middlewares.DataMiddleware({"scheduler": scheduler}))
    dp.errors.register(ui_error_handler, ExceptionTypeFilter(UnknownIntent))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
