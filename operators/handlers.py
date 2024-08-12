import datetime
from typing import Any

import config
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from apscheduler.schedulers.asyncio import AsyncIOScheduler, asyncio
from db.service import TaskService
from jobs import closed_task


async def on_type(
    callback: CallbackQuery, select, dialog_manager: DialogManager, c_type: str, /
):
    dialog_manager.dialog_data["c_type"] = c_type
    await dialog_manager.next()


async def on_close(message: Message, widget: Any, manager: DialogManager):
    taskid = manager.start_data.get("taskid", '')
    operator = config.AGREEMENTERS.get(message.from_user.id, "")
    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
    summary = message.text if message.text and len(message.text) > 1 else ""
    summary += f"\nзакрыл {operator}."
    TaskService.update_summary(taskid, summary)
    
    if TaskService.get_stored_taskid(taskid):
        TaskService.reopen(taskid)

    if (
        manager.start_data["status"] == "проверка"
        or not manager.start_data["act"]
    ):
        TaskService.change_status(taskid, "закрыто")
        job = scheduler.get_job(job_id=str(taskid))
        if job:
            job.remove()
        messaga = await message.answer("Заявка перемещена в архив.")
        await asyncio.sleep(3)
        await messaga.delete()
        slave = manager.start_data["slave"]
        task = manager.start_data["title"]
        taskid = manager.start_data["taskid"]
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


async def delay_handler(
    message: Message, message_input: MessageInput, manager: DialogManager
):
    delay = int(message.text) if message.text else 0
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

async def on_remove(callback: CallbackQuery, button, dialog_manager: DialogManager):
    TaskService.remove_task(dialog_manager.start_data.get('taskid'))
    await callback.answer('Заявка удалена', show_alert=True)
    try:
        await dialog_manager.done()
    except IndexError:
        await dialog_manager.done()
