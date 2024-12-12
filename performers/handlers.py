import datetime

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
from db.service import employee_service, journal_service, task_service
from notifications import confirmed_task_notification
from tasks import states as tsk_states


async def on_archive(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(
        state=tsk_states.TasksSG.tasks,
        data={
            "wintitle": config.TasksTitles.ARCHIVE,
            "userid": callback.from_user.id,
        },
    )


async def act_handler(msg: Message, widget, manager: DialogManager):
    new_actid = msg.photo[-1].file_id or ""
    old_actid = manager.start_data.get("actid") or ""
    manager.start_data.update(actid=f"{old_actid},{new_actid}".strip(","))
    await manager.next()


async def pin_videoreport(message: Message, message_input, manager: DialogManager):
    new_resultid = message.video.file_id
    old_resultid = manager.start_data.setdefault("resultid") or ""
    manager.start_data.update(resultid=f"{old_resultid},{new_resultid}".strip(","))
    await manager.next()


async def on_close(callback: CallbackQuery, button, manager: DialogManager):
    data = {
        **{key: manager.start_data[key] for key in ("taskid", "resultid", "actid")},
        "status": config.TasksStatuses.PERFORMED,
    }
    task_service.update(**data)

    note = manager.dialog_data.get("note", "")
    perf_record = f"выполнено, {manager.start_data.get('username')}\n{note}".strip()
    recdata = {
        "dttm": manager.start_data.get("performed_time"),
        "task": manager.start_data.get("taskid"),
        "employee": manager.start_data.get("userid"),
    }
    left_record = f"{manager.start_data.get('name')} Уехал"
    for rec in (perf_record, left_record):
        recdata.update(record=rec)
        journal_service.new(**recdata)

    last_rec = journal_service.get_last(callback.from_user.id)
    if last_rec and left_record == last_rec.get("record"):
        journal_service.delete(last_rec.get("recordid"))

    operators_ids = [
        operator["userid"]
        for operator in employee_service.get_by_filters(position="operator")
    ]
    slave = manager.start_data["username"]
    task = manager.start_data["title"]
    taskid = manager.start_data["taskid"]
    await confirmed_task_notification(operators_ids, slave, task, taskid)
    await manager.done()


async def on_cancel(clb, button, manager: DialogManager):
    task_service.update(
        taskid=manager.start_data.get("taskid"), status=config.TasksStatuses.AT_WORK
    )


async def pin_text(message: Message, message_input, manager: DialogManager):
    manager.dialog_data["note"] = message.text
    await manager.back()
