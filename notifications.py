from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.executors.base import logging
from apscheduler.schedulers.asyncio import asyncio
from pydantic import ValidationError

from config import CHIEF_ID
from custom.bot import MyBot
from db.service import employee_service

logger = logging.getLogger(__name__)


class TaskFactory(CallbackData, prefix="taskfctr"):
    task: str


async def base_notification(
    user: str | int, taskid: str | int, notification: str, msg_deleting=False
):
    bot: Bot = MyBot.get_instance()
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Хорошо", callback_data=TaskFactory(task=str(taskid)))

    try:
        messaga = await bot.send_message(
            chat_id=user,
            text=notification,
            reply_markup=keyboard.as_markup(),
        )
        if msg_deleting:
            await asyncio.sleep(300)
            await messaga.delete()

    except TelegramBadRequest as BadRqst:
        employee = employee_service.get_one(user)["username"]
        logger.info(
            f"Сообщение {notification} уже было удалено пользователем {employee}:\n",
            str(BadRqst),
        )
    except ValidationError:
        pass
    except TelegramForbiddenError as errr:
        logger.error(f"{notification}:\nОшибка отправки: {str(errr)}")


async def new_task_notification(
    users: list | tuple, task_title: str, taskid: int | str
):
    notification = f"Новая заявка: {task_title}"
    for user in users:
        await base_notification(user, taskid, notification)


async def confirmed_task_notification(operators, slave, title, taskid):
    text = f"{slave} выполнил заявку {title}."
    for operator in operators:
        await base_notification(operator, taskid, text)


async def closed_task_notification(performer, task_title, taskid):
    text = f"Заявка {task_title} закрыта и перемещена в архив."
    await base_notification(performer, taskid, text)


async def returned_task(performer, task, taskid):
    text = f"Заявка {task} возвращена вам в работу."
    await base_notification(performer, taskid, text)


async def check_work_execution(performer_id: str | int):
    users = [
        user["userid"] for user in employee_service.get_by_filters(position="operator")
    ]
    performer = employee_service.get_one(performer_id)
    text = f"{performer['username']} уже 30 минут на объекте, необходимо ему позвонить!"
    
    nots = []
    for user in users:
        asyncio.create_task(base_notification(user, "", text, msg_deleting=True))
    
    for note in nots:
        await note


async def new_customer_task_notification(customer: dict):
    text = f"Новая заявка от клиента: {customer.get('name', '')}, {customer.get('object', '')}"
    operators = [
        operator["userid"]
        for operator in employee_service.get_by_filters(position="operator")
    ]
    for operator in operators:
        await base_notification(operator, "", text)


async def cust_task_isclosed_notification(customer_id: int | str, task_title: str):
    text = f"Заявка '{task_title}' выполнена."
    await base_notification(customer_id, "", text)


async def journal_reminder():
    message_text = "Не забываем отмечаться в журнале!"
    users = [user["userid"] for user in employee_service.get_all()]
    ignored_users = {1740579878, CHIEF_ID}
    users = [user for user in users if user not in ignored_users]
    for user in users:
        await base_notification(user, "", message_text)
