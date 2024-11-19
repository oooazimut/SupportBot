import asyncio
import logging

from aiogram import Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.types import ErrorEvent
from aiogram_dialog import DialogManager, StartMode, setup_dialogs
from aiogram_dialog.api.exceptions import OutdatedIntent, UnknownIntent
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from redis.asyncio.client import Redis

import config
import jobs
import middlewares
from custom.bot import MyBot
from db.schema import CREATE_DB_SCRIPT
from db.service import employee_service
from db.tools import create_db
from journal import dialogs as jrn_dialogs
from observers import dialogs as ob_dialogs
from operators import dialogs as op_dialogs
from performers import dialogs as prf_dialogs
from routers import finish_router, start_router
from tasks import dialogs as tsk_dialogs  # noqa: F401
from customers import dialogs as cust_dialogs


async def ui_error_handler(event: ErrorEvent, dialog_manager: DialogManager):
    userid = dialog_manager.middleware_data["event_from_user"].id
    user = employee_service.get_employee(userid=userid)
    if user:
        position = user["position"]
    else:
        position = "customer"
    await dialog_manager.start(
        state=config.START_STATES[position], mode=StartMode.RESET_STACK
    )


async def main():
    logging.basicConfig(
        level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s"
    )
    create_db(script=CREATE_DB_SCRIPT)
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
        tsk_dialogs.new,
        tsk_dialogs.tasks,
        tsk_dialogs.media,
        tsk_dialogs.filtration,
    )
    dp.include_routers(jrn_dialogs.main, jrn_dialogs.search)
    dp.include_router(ob_dialogs.main)
    dp.include_routers(
        cust_dialogs.main_dialog,
        cust_dialogs.new_customer,
        cust_dialogs.new_task,
    )
    dp.include_router(finish_router.router)
    scheduler = AsyncIOScheduler()
    scheduler.add_jobstore(
        "redis", jobs_key="example.jobs", run_times_key="example.run_times"
    )
    scheduler.start()
    scheduler.add_job(
        func=jobs.two_reports,
        trigger="cron",
        day_of_week="mon-sat",
        hour=7,
        id="gen_report",
        replace_existing=True,
    )
    scheduler.add_job(
        jobs.journal_reminder,
        "cron",
        day_of_week="mon-fri",
        hour=8,
        minute=30,
        id="morning_reminder",
        replace_existing=True,
    )
    scheduler.add_job(
        jobs.journal_reminder,
        "cron",
        day_of_week="mon-fri",
        hour=16,
        id="evening_reminder",
        replace_existing=True,
    )
    setup_dialogs(dp)
    dp.update.outer_middleware(middlewares.DataMiddleware({"scheduler": scheduler}))
    dp.errors.register(
        ui_error_handler, ExceptionTypeFilter(UnknownIntent, OutdatedIntent)
    )
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
