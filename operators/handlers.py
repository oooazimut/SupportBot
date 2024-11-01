import datetime
from typing import Any

from apscheduler.executors.base import logging

import config
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler, asyncio
from db.service import journal_service, task_service
from jobs import closed_task_notification


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
    media_type = message.content_type

    if media_type in config.CONTENT_ATTR_MAP:
        media_id, txt = config.CONTENT_ATTR_MAP[media_type](message)
    else:
        media_id, txt = None, ""

    media_type = media_type.value if media_id else None

    manager.dialog_data.update({"summary": txt or ""})
    manager.start_data.update({
        "media_id": f'{media_id or ""},{manager.start_data.get("media_id") or ""}'.strip(","),
        "media_type": f'{media_type or ""},{manager.start_data.get("media_type") or ""}'.strip(
            ","
        ),
    })
    await message.answer("Добавлено")
    await asyncio.sleep(1)
    await manager.back()


async def on_close(callback: CallbackQuery, widget: Any, manager: DialogManager):
    taskid = manager.start_data.get("taskid", "")
    operator = config.AGREEMENTERS.get(callback.from_user.id, "")
    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
    current_dttm = datetime.datetime.now().replace(microsecond=0)

    recdata = {
        "dttm": current_dttm,
        "task": manager.start_data.get("taskid"),
        "employee": manager.start_data.get("userid"),
    }

    task_service.change_dttm(taskid, datetime.datetime.now())

    is_checking = (
        manager.start_data["status"] == "проверка" or not manager.start_data["act"]
    )
    new_status = "закрыто" if is_checking else "проверка"
    manager.start_data.update({"status": new_status})

    task_service.update_task(manager.start_data)

    if new_status == "закрыто":
        job = scheduler.get_job(job_id=str(taskid))
        if job:
            job.remove()

        slave = manager.start_data.get("slave")
        if slave:
            task_title = manager.start_data["title"]
            await closed_task_notification(slave, task_title, taskid)

    message_text = (
        "Заявка перемещена в архив."
        if new_status == "закрыто"
        else "Заявка ушла на проверку правильного заполнения акта."
    )
    await callback.answer(message_text, show_alert=True)

    action = "закрыл" if new_status == "закрыто" else "отправил на проверку"
    recdata["record"] = f"{action} {operator}\n{manager.dialog_data.get('summary') or ''}"
    journal_service.new_record(recdata)
    if manager.dialog_data.get('summary'):
        del manager.dialog_data["summary"]

    if manager.dialog_data.get("closing_type") == "частично":
        task_service.reopen_task(taskid)

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

    task_service.change_status(taskid, status="отложено")
    scheduler.add_job(
        task_service.change_status,
        trigger="date",
        run_date=datetime.datetime(year, month, day, 9, 0, 0),
        args=[taskid, delayed_status],
        id="delay" + str(taskid),
    )
    await manager.done()
    messaga = await message.answer(f"Ваша заявка отложена до {trigger_data}")
    await asyncio.sleep(5)
    await messaga.delete()


async def on_remove(callback: CallbackQuery, button, dialog_manager: DialogManager):
    task_service.remove_task(dialog_manager.start_data.get("taskid"))
    await callback.answer("Заявка удалена", show_alert=True)
    try:
        await dialog_manager.done()
    except IndexError:
        await dialog_manager.done()
