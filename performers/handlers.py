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


async def act_handler(msg: Message, widget: MessageInput, manager: DialogManager):
    actid = None
    acttype = msg.content_type
    match acttype:
        case "document":
            actid = msg.document.file_id
        case "photo":
            actid = msg.photo[-1].file_id

    data = {
        "taskid": manager.start_data.get("taskid"),
        "actid": actid,
        "acttype": acttype,
    }

    TaskService.add_act(data)
    await manager.next()


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


async def pin_videoreport(
    message: Message,
    message_input,
    manager: DialogManager,
):
    media_id = message.video.file_id
    TaskService.update_result(media_id, manager.start_data["taskid"])
    await manager.next()


async def on_close(callback: CallbackQuery, button, manager: DialogManager):
    taskid = manager.start_data["taskid"]
    task = TaskService.get_task(taskid)[0]
    run_date = datetime.datetime.now() + datetime.timedelta(days=3)
    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]

    TaskService.change_status(taskid, "выполнено")
    if (
        manager.dialog_data.get("closing_type") == "частично"
        and task.get("status") != "проверка"
    ):
        TaskService.store_taskid(taskid)

    recdata = {
        "dttm": datetime.datetime.now().strftime("%Y-%m-%d"),
        "task": manager.start_data.get("taskid"),
        "employee": manager.start_data.get("userid"),
        "record": f'выполнено {manager.dialog_data.get("closing_type")}, {manager.start_data.get("username")}',
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

    text = f'Заявка {manager.start_data["title"]} выполнена. Ожидается подтверждение закрытия от оператора или клиента.'
    callback.answer(text, show_alert=True)
