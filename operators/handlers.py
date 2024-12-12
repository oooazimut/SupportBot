import datetime
from typing import Any

from apscheduler.executors.base import logging


import config
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler, asyncio
from db.service import customer_service, journal_service, task_service
from jobs import handle_description
from notifications import closed_task_notification, cust_task_isclosed_notification

logger = logging.getLogger(__name__)


async def on_type(
    callback: CallbackQuery, select, dialog_manager: DialogManager, c_type: str, /
):
    dialog_manager.dialog_data["c_type"] = c_type
    await dialog_manager.next()


async def on_closing_type(
    callback: CallbackQuery, select, dialog_manager: DialogManager, c_type: str, /
):
    dialog_manager.dialog_data["closing_type"] = (
        "полностью" if int(c_type) else "частично"
    )
    await dialog_manager.next()


async def summary_handler(message: Message, message_input, manager: DialogManager):
    task: dict = manager.start_data
    handle_description(message, task)


async def on_close(callback: CallbackQuery, widget: Any, manager: DialogManager):
    taskid = manager.start_data.get("taskid", "")
    customer = customer_service.get_one(manager.start_data.get("creator"))
    operator = config.AGREEMENTERS.get(callback.from_user.id, "")
    current_dttm = datetime.datetime.now().replace(microsecond=0)

    to_archive = (
        manager.start_data["status"] == config.TasksStatuses.CHECKED
        or not manager.start_data["act"]
    )
    new_status = (
        config.TasksStatuses.ARCHIVE if to_archive else config.TasksStatuses.CHECKED
    )
    manager.start_data.update(status=new_status, created=current_dttm)
    task_keys = task_service.get_keys()
    data = {key: value for key, value in manager.start_data.items() if key in task_keys}
    task_service.update(**data)

    if new_status == config.TasksStatuses.ARCHIVE and manager.start_data.get("slave"):
        await closed_task_notification(
            manager.start_data["slave"],
            manager.start_data["title"],
            taskid,
        )

    recdata = {
        "dttm": current_dttm,
        "task": manager.start_data.get("taskid"),
        "employee": manager.start_data.get("userid"),
    }
    action = (
        "закрыл"
        if new_status == config.TasksStatuses.ARCHIVE
        else "отправил на проверку"
    )
    recdata["record"] = f"{action} {operator}"
    journal_service.new(**recdata)

    if manager.dialog_data.get("closing_type") == "частично":
        task_service.reopen_task(taskid)

    if customer:
        await cust_task_isclosed_notification(
            customer.get("id"),
            manager.start_data.get("title", ""),
        )

    message_text = (
        "Заявка перемещена в архив."
        if new_status == "закрыто"
        else "Заявка ушла на проверку правильного заполнения акта."
    )
    await callback.answer(message_text, show_alert=True)
    await manager.done()


async def delay_handler(
    message: Message, message_input: MessageInput, manager: DialogManager
):
    delay = int(message.text) if message.text else 0
    taskid = manager.start_data["taskid"]
    delayed_status = manager.start_data["status"]
    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
    trigger_data = datetime.date.today() + datetime.timedelta(days=delay)
    year, month, day = trigger_data.year, trigger_data.month, trigger_data.day

    task_service.update(taskid=taskid, status=config.TasksStatuses.DELAYED)
    scheduler.add_job(
        task_service.update,
        trigger="date",
        run_date=datetime.datetime(year, month, day, 9, 0, 0),
        kwargs={"taskid": taskid, "status": delayed_status},
        id="delay" + str(taskid),
    )
    await manager.done()
    messaga = await message.answer(f"Ваша заявка отложена до {trigger_data}")
    await asyncio.sleep(5)
    await messaga.delete()


async def on_remove(callback: CallbackQuery, button, dialog_manager: DialogManager):
    title = dialog_manager.start_data.get("title")
    task_service.delete(dialog_manager.start_data.get("taskid"))
    await callback.answer("Заявка удалена", show_alert=True)
    try:
        await dialog_manager.done()
    except (IndexError, TypeError) as Errr:
        logger.info(f"Заявка {title} была удалена:\n", str(Errr))
        await dialog_manager.done()
