from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, StartMode
from apscheduler.executors.base import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import START_STATES
from db.service import employee_service, task_service
from notifications import TaskFactory

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, dialog_manager: DialogManager):
    bot = dialog_manager.middleware_data["bot"]
    txt = f"Пользователь {message.from_user.full_name} {message.from_user.id} запустил бота"
    await bot.send_message(chat_id=5963726977, text=txt)

    user = employee_service.get_employee(userid=message.from_user.id)
    if user:
        position = user["position"]
    else:
        position = "customer"
    await dialog_manager.start(state=START_STATES[position], mode=StartMode.RESET_STACK)


@router.callback_query(TaskFactory.filter())
async def switch_off_notification(
    callback: CallbackQuery, callback_data: TaskFactory, scheduler: AsyncIOScheduler
):
    if callback_data.task:
        jobid = str(callback.from_user.id) + callback_data.task
        job = scheduler.get_job(jobid)

        if job:
            job.remove()

    task = task_service.get_task(callback_data.task)
    if (
        task
        and int(callback.from_user.id) == task["slave"]
        and task["status"] == "назначено"
    ):
        task_service.change_status(callback_data.task, "в работе")
        await callback.answer(text="заявка принята в работу", show_alert=True)

    if callback.message and isinstance(callback.message, Message):
        try:
            await callback.message.delete()
        except TelegramBadRequest as errr:
            logging.error("Сообщение невозможно удалить:", str(errr))
    else:
        logger.warning("Оповещение для удаления отсутствует")
        logger.warning(callback.from_user.full_name, callback.from_user.id)
        logger.warning(callback.message.text)


@router.callback_query(F.data == "agr_not_is_readed")
async def del_message(callback: CallbackQuery):
    await callback.message.delete()
