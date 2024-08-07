import datetime
import sqlite3
from performers import states as prf_states
from typing import Any


from aiogram import Bot
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from aiogram.utils.formatting import Bold, Text
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot import MyBot
from db.service import EmployeeService, EntityService, TaskService
from jobs import new_task
from operators.states import OpDelayingSG, OpCloseTaskSG

from . import states


async def on_task(
    callback: CallbackQuery, widget: Any, manager: DialogManager, taskid: str
):
    manager.dialog_data["taskid"] = taskid
    await manager.switch_to(states.TasksSG.task)


async def edit_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(states.NewSG.preview, data=manager.dialog_data["task"])


async def on_delay(callback, button, manager: DialogManager):
    task = manager.dialog_data["task"].copy()
    await manager.start(state=OpDelayingSG.main, data=task)


async def next_or_end(event, widget, dialog_manager: DialogManager, *_):
    if dialog_manager.dialog_data.get("finished"):
        await dialog_manager.switch_to(states.NewSG.preview)
    else:
        await dialog_manager.next()


async def on_priority(event, select, dialog_manager: DialogManager, data: str, /):
    dialog_manager.dialog_data["task"]["priority"] = data
    await next_or_end(event, select, dialog_manager)


async def on_act(event, select, dialog_manager: DialogManager, data, /):
    dialog_manager.dialog_data["task"]["act"] = data
    await next_or_end(event, select, dialog_manager)


async def on_entity(event, select, dialog_manager: DialogManager, ent_id: str, /):
    entity = EntityService.get_entity(ent_id)[0]
    dialog_manager.dialog_data["task"]["entity"] = entity["ent_id"]
    dialog_manager.dialog_data["task"]["name"] = entity["name"]
    await next_or_end(event, select, dialog_manager)


async def on_slave(event, select, dialog_manager: DialogManager, data: str, /):
    dialog_manager.dialog_data["task"]["slave"] = data
    user = EmployeeService.get_employee(data)
    dialog_manager.dialog_data["task"]["username"] = user.get("username")
    await next_or_end(event, select, dialog_manager)


async def on_agreementer(event, select, dialog_manager: DialogManager, data: str, /):
    dialog_manager.dialog_data["task"]["agreement"] = data
    await next_or_end(event, select, dialog_manager)


async def task_description_handler(
    message: Message, message_input: MessageInput, manager: DialogManager
):
    def is_empl(userid):
        user = EmployeeService.get_employee(userid)
        if user:
            return True

    txt = ""
    media_id = None
    match message.content_type:
        case ContentType.TEXT:
            txt = message.text
        case ContentType.PHOTO:
            media_id = message.photo[-1].file_id
            txt = message.caption
        case ContentType.DOCUMENT:
            media_id = message.document.file_id
            txt = message.caption
        case ContentType.VIDEO:
            media_id = message.video.file_id
            txt = message.caption
        case ContentType.AUDIO:
            media_id = message.audio.file_id
            txt = message.caption
        case ContentType.VOICE:
            media_id = message.voice.file_id
        case ContentType.VIDEO_NOTE:
            media_id = message.video_note.file_id
    media_type = message.content_type
    manager.dialog_data["task"]["description"] = txt
    manager.dialog_data["task"]["media_id"] = media_id
    manager.dialog_data["task"]["media_type"] = media_type

    if is_empl(message.from_user.id) and not manager.dialog_data.get("finished"):
        await manager.next()
    else:
        await manager.switch_to(states.NewSG.preview)


async def ent_name_handler(
    message: Message, message_input: MessageInput, manager: DialogManager
):
    manager.dialog_data["subentity"] = message.text
    await manager.next()


async def on_confirm(clb: CallbackQuery, button: Button, manager: DialogManager):
    def is_exist(someone_task: dict):
        return someone_task.get("taskid") is not None

    data: dict = manager.dialog_data.get("task", {})
    data.setdefault("created", datetime.datetime.now().replace(microsecond=0))
    data.setdefault("creator", clb.from_user.id)
    if data.get("slave"):
        data["status"] = "назначено"
    data.setdefault("status", "открыто")
    data.setdefault("slave", None)
    data.setdefault("entity", None)
    data.setdefault("agreement", None)
    data.setdefault("priority", None)
    if is_exist(data):
        TaskService.update_task(data)
        scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
        job = scheduler.get_job(job_id="delay" + str(data["taskid"]))
        if job:
            job.remove()
        await clb.answer("Заявка отредактирована.", show_alert=True)
    else:
        task = TaskService.save_task(data)
        await clb.answer(
            "Заявка принята в обработку и скоро появится в списке заявок объекта.",
            show_alert=True,
        )
        users = EmployeeService.get_employees_by_position("operator")
        userids = [user["userid"] for user in users]
        slaveid = data.get("slave")
        if slaveid:
            userids.append(slaveid)

        scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
        for userid in userids:
            scheduler.add_job(
                new_task,
                "interval",
                minutes="5",
                next_run_time=datetime.datetime.now(),
                args=[userid, task["title"], task["taskid"]],
                id=str(userid) + str(task["taskid"]),
                replace_existing=True,
            )

    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


async def on_start(data, manager: DialogManager):
    if manager.start_data:
        manager.dialog_data["task"] = manager.start_data
    else:
        manager.dialog_data["task"] = dict()


async def on_return(clb: CallbackQuery, button, manager: DialogManager):
    taskid = manager.dialog_data.get("task", {}).get("taskid")
    task = TaskService.get_task(taskid)[0]
    if task["slave"]:
        TaskService.change_status(taskid, "в работе")
    else:
        TaskService.change_status(taskid, "открыто")
    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
    job = scheduler.get_job(str(taskid))
    if job:
        job.remove()
        await clb.answer("Заявка возвращена в работу.", show_alert=True)
    else:
        await clb.answer("Заявка уже в работе.", show_alert=True)
    await manager.done()


async def on_del_performer(clb: CallbackQuery, button, manager: DialogManager):
    manager.dialog_data["task"]["slave"] = None
    manager.dialog_data["task"]["username"] = None
    await clb.answer("Исполнитель убран из заявки.", show_alert=True)


async def accept_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    agreement = manager.dialog_data.get("task", {}).get("agreement")
    if agreement:
        await callback.answer(f"Требуется согласование c {agreement}!", show_alert=True)
        bot: Bot = MyBot.get_instance()
        operators: list = EmployeeService.get_employees_by_position("operator") or []
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Хорошо", callback_data="agr_not_is_readed")
        content = Text(
            Bold(
                f'{agreement} нужно согласование с {manager.dialog_data.get("task", {}).get("username")} по заявке {manager.dialog_data.get("task", {}).get("title")}!'
            )
        )
        for operator in operators:
            try:
                await bot.send_message(
                    chat_id=operator["userid"],
                    **content.as_kwargs(),
                    reply_markup=keyboard.as_markup(),
                )
            except TelegramBadRequest:
                pass
        return

    TaskService.change_status(
        manager.dialog_data.get("task", {}).get("taskid"), "в работе"
    )
    await callback.answer(
        f'Заявка {manager.dialog_data.get("task", {}).get("title")} принята в работу.'
    )
    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


async def on_perform(callback: CallbackQuery, button: Button, manager: DialogManager):
    data = manager.dialog_data.get("task", {})
    if data.get("act"):
        await manager.start(prf_states.PrfPerformedSG.pin_act, data=data)
    else:
        await manager.start(prf_states.PrfPerformedSG.pin_videoreport, data=data)


async def get_back(callback: CallbackQuery, button: Button, manager: DialogManager):
    TaskService.change_status(
        manager.dialog_data.get("task", {}).get("taskid"), "в работе"
    )
    await callback.answer(
        f'Заявка {manager.dialog_data.get("task", {}).get("title")} снова в работе.'
    )


async def show_operator_media(callback: CallbackQuery, button, manager: DialogManager):
    mediatype = manager.dialog_data.get("task", {}).get("media_type")
    mediaid = manager.dialog_data.get("task", {}).get("media_id")
    await manager.start(
        state=states.MediaSG.main,
        data={"type": mediatype, "id": mediaid, "wintitle": "Медиа от оператора"},
    )


async def show_performer_media(callback: CallbackQuery, button, manager: DialogManager):
    mediatype = manager.dialog_data.get("task", {}).get("resulttype")
    mediaid = manager.dialog_data.get("task", {}).get("resultid")
    await manager.start(
        state=states.MediaSG.main,
        data={
            "type": mediatype,
            "id": mediaid,
            "wintitle": "Медиа от исполнителя",
        },
    )


async def show_act(callback: CallbackQuery, button, manager: DialogManager):
    mediatype = manager.dialog_data.get("task", {}).get("acttype")
    mediaid = manager.dialog_data.get("task", {}).get("actid")
    await manager.start(
        state=states.MediaSG.main,
        data={"type": mediatype, "id": mediaid, "wintitle": "Акт"},
    )


async def on_close(callback: CallbackQuery, button, manager: DialogManager):
    await manager.start(
        state=OpCloseTaskSG.type_choice,
        data={"taskid": manager.dialog_data.get("taskid")},
    )
