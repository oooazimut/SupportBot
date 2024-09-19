import datetime

import config
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db.service import EmployeeService, JournalService, TaskService
from jobs import close_task, confirmed_task
from tasks import states as tsk_states


async def on_archive(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(
        state=tsk_states.TasksSG.tasks,
        data={
            "wintitle": config.TasksTitles.ARCHIVE.value,
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
    print(manager.start_data.get("performed_time"))
    taskid = manager.start_data["taskid"]
    run_date = datetime.datetime.now() + datetime.timedelta(days=3)
    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]

    if manager.dialog_data.get("actid"):
        actid = ",".join(manager.dialog_data["actid"])
        TaskService.add_act({"taskid": taskid, "actid": actid})
    resultid = ",".join(manager.dialog_data.get("resultid", []))
    TaskService.update_result(resultid, taskid)
    TaskService.change_status(taskid, "выполнено")

    note = manager.dialog_data.get("note", "")
    record = f'выполнено, {manager.start_data.get("username")}'
    if note:
        record += f"\n{note}"
    recdata = {
        "dttm": manager.start_data.get("performed_time"),
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


async def on_cancel(clb, button, manager: DialogManager):
    TaskService.change_status(
        manager.start_data.get("taskid"), config.TasksStatuses.AT_WORK.value
    )


async def pin_text(message: Message, message_input, manager: DialogManager):
    manager.dialog_data["note"] = message.text
    await manager.back()
