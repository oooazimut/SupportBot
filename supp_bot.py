import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram_dialog import setup_dialogs

import config
from db.db_models import SqLiteDataBase
from db.service import TaskService, EmployeeService
from routers import start_router, finish_router
from dialogs import customer

_logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

db = SqLiteDataBase('Support.db')
task_service = TaskService(db)
empl_service = EmployeeService(db)


async def main():
    bot = Bot(config.TOKEN)
    dp = Dispatcher()
    dp.include_routers(start_router.router, customer.main_dialog, customer.create_task_dialog,
                       finish_router.router)
    setup_dialogs(dp)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
