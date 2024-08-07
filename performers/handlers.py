import datetime

import config
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from apscheduler.schedulers.asyncio import AsyncIOScheduler, asyncio
from db.service import EmployeeService, EntityService, TaskService
from jobs import close_task, confirmed_task
from tasks import states as tsk_states

from . import states


async def on_archive(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(
        state=tsk_states.TasksSG.tasks,
        data={"wintitle": config.TasksTitles.ARCHIVE, "userid": callback.from_user.id},
    )


async def entites_name_handler(
    message: Message, message_input: MessageInput, manager: DialogManager
):
    entities = EntityService.get_entities_by_substr(message.text)
    if entities:
        manager.dialog_data["entities"] = entities
        await manager.switch_to(states.PrfMainMenuSG.entities)
    else:
        pass


async def on_entity(callback: CallbackQuery, select, manager: DialogManager, entid, /):
    await manager.start(
        tsk_states.TasksSG.tasks,
        data={"wintitle": config.TasksTitles.ENTITY, "entid": entid},
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


async def pin_videoreport(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
    callback=CallbackQuery,
):
    txt = message.caption
    media_id = message.video.file_id
    media_type = message.content_type
    TaskService.save_result(txt, media_id, media_type, manager.start_data["taskid"])

    taskid = manager.start_data["taskid"]
    run_date = datetime.datetime.now() + datetime.timedelta(days=3)
    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]

    TaskService.change_status(taskid, "выполнено")
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
    mes = await message.answer(text=text)
    await asyncio.sleep(5)
    await mes.delete()
    await manager.done()
