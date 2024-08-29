import datetime

import config
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from apscheduler.schedulers.asyncio import AsyncIOScheduler, asyncio
from db.service import EmployeeService, EntityService, JournalService, TaskService
from jobs import close_task, confirmed_task
from tasks import states as tsk_states

from . import states


async def on_archive(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(
        state=tsk_states.TasksSG.tasks,
        data={
            "wintitle": config.TasksTitles.ARCHIVE.value,
            "userid": callback.from_user.id,
        },
    )


async def on_closing_type(
    callback: CallbackQuery, select, dialog_manager: DialogManager, c_type: str, /
):
    act = dialog_manager.start_data.get("act")
    dialog_manager.dialog_data["closing_type"] = (
        "полностью" if int(c_type) else "частично"
    )

    if act:
        await dialog_manager.next()
    else:
        await dialog_manager.switch_to(state=states.PrfPerformedSG.pin_videoreport)


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

    if manager.dialog_data.get("actid"):
        actid = ",".join(manager.dialog_data["actid"])
        TaskService.add_act({"taskid": taskid, "actid": actid})
    resultid = ",".join(manager.dialog_data["resultid"])
    TaskService.update_result(resultid, taskid)
    TaskService.change_status(taskid, "выполнено")

    note = manager.dialog_data.get("note", "")
    record = f'выполнено {manager.dialog_data.get("closing_type")}, {manager.start_data.get("username")}'
    if note:
        record += f"\n{note}"
    recdata = {
        "dttm": datetime.datetime.now().strftime("%Y-%m-%d"),
        "task": manager.start_data.get("taskid"),
        "employee": manager.start_data.get("userid"),
        "record": record,
    }
    JournalService.new_record(recdata)

    if not manager.start_data["act"]:
        scheduler.add_job(
            close_task,
            trigger="date",
            run_date=run_date,
            args=[taskid],
            id=str(taskid),
            replace_existing=True,
        )

    operators = EmployeeService.get_employees_by_position("operator")
    for o in operators:
        operatorid = o["userid"]
        slave = manager.start_data["username"]
        task = manager.start_data["title"]
        taskid = manager.start_data["taskid"]
        scheduler.add_job(
            confirmed_task,
            "interval",
            minutes=5,
            next_run_time=datetime.datetime.now(),
            args=[operatorid, slave, task, taskid],
            id=str(operatorid) + str(taskid),
            replace_existing=True,
        )

    # text = f'Заявка {manager.start_data["title"]} выполнена. Ожидается подтверждение закрытия от оператора или клиента.'
    # await callback.answer(text, show_alert=True)


async def pin_text(message: Message, message_input, manager: DialogManager):
    manager.dialog_data["note"] = message.text
    await manager.back()
