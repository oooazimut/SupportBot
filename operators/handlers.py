import datetime
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from apscheduler.schedulers.asyncio import AsyncIOScheduler, asyncio

import config
from db.service import TaskService
from jobs import closed_task, returned_task

from . import states


async def on_act(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(OpTaskSG.act, show_mode=ShowMode.DELETE_AND_SEND)


async def on_back_to_preview(callback, button, manager: DialogManager):
    await manager.switch_to(OpTaskSG.preview, show_mode=ShowMode.SEND)


async def on_type(
    callback: CallbackQuery, select, dialog_manager: DialogManager, c_type: str, /
):
    dialog_manager.dialog_data["c_type"] = c_type
    await dialog_manager.next()


async def on_close(message: Message, widget: Any, manager: DialogManager):
    taskid = manager.dialog_data["task"]["taskid"]
    operator = config.AGREEMENTERS.get(message.from_user.id)
    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
    summary = manager.dialog_data.get("task", {}).get("summary") or ""
    add_summary = message.text if len(message.text) > 1 else ""
    summary += add_summary + f"\nзакрыл {operator}.\n"
    TaskService.update_summary(taskid, summary)

    if manager.dialog_data.get("c_type") == "0":
        TaskService.reopen(taskid)

    if (
        manager.dialog_data["task"]["status"] == "проверка"
        or not manager.dialog_data["task"]["act"]
    ):
        TaskService.change_status(taskid, "закрыто")
        job = scheduler.get_job(job_id=str(taskid))
        if job:
            job.remove()
        messaga = await message.answer("Заявка перемещена в архив.")
        await asyncio.sleep(3)
        await messaga.delete()
        slave = manager.dialog_data["task"]["slave"]
        task = manager.dialog_data["task"]["title"]
        taskid = manager.dialog_data["task"]["taskid"]
        if slave:
            scheduler.add_job(
                closed_task,
                "interval",
                minutes=5,
                next_run_time=datetime.datetime.now(),
                args=[slave, task, taskid],
                id=str(slave) + str(taskid),
                replace_existing=True,
            )
    else:
        TaskService.change_status(taskid, "проверка")
        messaga = await message.answer(
            "Заявка ушла на проверку правильного заполнения акта."
        )
        await asyncio.sleep(3)
        await messaga.delete()

    await manager.done()


async def on_return(clb: CallbackQuery, button, manager: DialogManager):
    task = manager.dialog_data["task"]
    TaskService.change_status(task["taskid"], "в работе")

    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
    job = scheduler.get_job(str(task["taskid"]))
    if job:
        job.remove()
        await clb.answer("Заявка возвращена в работу.", show_alert=True)
        slave = manager.dialog_data["task"]["slave"]
        task = manager.dialog_data["task"]["title"]
        taskid = manager.dialog_data["task"]["taskid"]
        scheduler.add_job(
            returned_task,
            "interval",
            minutes=5,
            next_run_time=datetime.datetime.now(),
            args=[slave, task, taskid],
            id=str(slave) + task,
            replace_existing=True,
        )
    else:
        await clb.answer("Заявка уже в работе.", show_alert=True)

    await manager.switch_to(OpTaskSG.opened_tasks)


async def delay_handler(
    message: Message, message_input: MessageInput, manager: DialogManager
):
    delay = int(message.text)
    taskid = manager.start_data["taskid"]
    delayed_status = manager.start_data["status"]
    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
    trigger_data = datetime.date.today() + datetime.timedelta(days=delay)
    year, month, day = trigger_data.year, trigger_data.month, trigger_data.day

    TaskService.change_status(taskid, status="отложено")
    scheduler.add_job(
        TaskService.change_status,
        trigger="date",
        run_date=datetime.datetime(year, month, day, 9, 0, 0),
        args=[taskid, delayed_status],
        id="delay" + str(taskid),
    )
    await manager.done()
    messaga = await message.answer(f"Ваша заявка отложена до {trigger_data}")
    await asyncio.sleep(5)
    await messaga.delete()
