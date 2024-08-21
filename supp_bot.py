import asyncio
import logging

from aiogram import Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.types import ErrorEvent
from aiogram_dialog import DialogManager, StartMode, setup_dialogs
from aiogram_dialog.api.exceptions import UnknownIntent
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis.asyncio.client import Redis

import config
from db.models import SqLiteDataBase
from db.schema import CREATE_DB_SCRIPT
from db.service import EmployeeService
import jobs
import middlewares
from custom.bot import MyBot
from routers import finish_router, start_router
from operators import dialogs as op_dialogs
from performers import dialogs as prf_dialogs
from tasks import dialogs as tsk_dialogs  # noqa: F401
from journal import dialogs as jrn_dialogs
from observers import dialogs as ob_dialogs

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


async def ui_error_handler(event: ErrorEvent, dialog_manager: DialogManager):
    userid = dialog_manager.middleware_data["event_from_user"].id
    user = EmployeeService.get_employee(userid=userid)
    if user:
        position = user["position"]
    else:
        position = "customer"
    await dialog_manager.start(
        state=config.START_STATES[position], mode=StartMode.RESET_STACK
    )


async def main():
    SqLiteDataBase.create(script=CREATE_DB_SCRIPT)
    bot = MyBot(config.TOKEN, parse_mode=ParseMode.HTML).get_instance()
    storage = RedisStorage(
        Redis(), key_builder=DefaultKeyBuilder(with_destiny=True, with_bot_id=True)
    )
    dp = Dispatcher(storage=storage)
    dp.include_router(start_router.router)
    dp.include_routers(
        op_dialogs.main,
        op_dialogs.tasks,
        op_dialogs.close_task,
        op_dialogs.delay,
        op_dialogs.remove,
    )
    dp.include_routers(prf_dialogs.main, prf_dialogs.performed)
    dp.include_routers(
        tsk_dialogs.new, tsk_dialogs.tasks, tsk_dialogs.media, tsk_dialogs.filtration
    )
    dp.include_routers(jrn_dialogs.main, jrn_dialogs.search)
    dp.include_router(ob_dialogs.main)
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
