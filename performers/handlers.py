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


async def act_handler(msg: Message, widget: MessageInput, manager: DialogManager):
    manager.dialog_data.setdefault("actid", []).insert(0, msg.photo[-1].file_id)
    await manager.next()


async def pin_videoreport(
    message: Message,
    message_input,
    manager: DialogManager,
):
    manager.dialog_data.setdefault("resultid", []).insert(0, message.video.file_id)
    await manager.next()


async def on_close(callback: CallbackQuery, button, manager: DialogManager):
    taskid = manager.start_data["taskid"]
    run_date = datetime.datetime.now() + datetime.timedelta(days=3)
    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
    task = task_service.get_one(taskid)

    resultid = ",".join(manager.dialog_data.get("resultid", []))
    if task.get("resultid"):
        resultid += f", {task.get('resultid')}"

    data = dict(taskid=taskid, resultid=resultid, status=config.TasksStatuses.PERFORMED)

    if manager.dialog_data.get("actid"):
        actid = ",".join(manager.dialog_data["actid"])
        if task.get("taskid"):
            actid += f", {task.get('actid')}"
        data.update(actid=actid)

    task_service.update(**data)

    note = manager.dialog_data.get("note", "")
    record = f"выполнено, {manager.start_data.get('username')}"
    if note:
        record += f"\n{note}"
    recdata = {
        "dttm": manager.start_data.get("performed_time"),
        "task": manager.start_data.get("taskid"),
        "employee": manager.start_data.get("userid"),
        "record": record,
    }
    journal_service.new(**recdata)

    record = f"{manager.start_data.get('name')} Уехал"

    last_rec = journal_service.get_last(callback.from_user.id)
    if last_rec and record == last_rec.get("record"):
        journal_service.delete(last_rec.get("recordid"))

    recdata["record"] = record
    journal_service.new(**recdata)

    if not manager.start_data["act"]:
        scheduler.add_job(
            task_service.update,
            trigger="date",
            run_date=run_date,
            kwargs={"taskid": taskid, "status": config.TasksStatuses.ARCHIVE},
            id=str(taskid),
            replace_existing=True,
        )

    operators_ids = [
        operator["userid"]
        for operator in employee_service.get_by_filters(position="operator")
    ]
    slave = manager.start_data["username"]
    task = manager.start_data["title"]
    taskid = manager.start_data["taskid"]
    await confirmed_task_notification(operators_ids, slave, task, taskid)
    # text = f'Заявка {manager.start_data["title"]} выполнена. Ожидается подтверждение закрытия от оператора или клиента.'
    # await callback.answer("", show_alert=True)
    await manager.done()


async def on_cancel(clb, button, manager: DialogManager):
    task_service.update(
        taskid=manager.start_data.get("taskid"), status=config.TasksStatuses.AT_WORK
    )


async def pin_text(message: Message, message_input, manager: DialogManager):
    manager.dialog_data["note"] = message.text
    await manager.back()
