import datetime
from typing import Any

from aiogram import Bot
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message
from aiogram.utils.formatting import Bold, Text
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import ChatEvent, DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Button,
    ManagedCheckbox,
    ManagedListGroup,
    ManagedRadio,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import TasksStatuses
from custom.bot import MyBot
from db.service import EmployeeService, EntityService, JournalService, TaskService
from jobs import new_task
from operators.states import OpCloseTaskSG, OpDelayingSG, OpRemoveTaskSG
from performers import states as prf_states

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


async def on_slave_choice(callback, button, dialog_manager: DialogManager):
    dialog_manager.dialog_data["task"]["slaves"] = list()
    slaves = EmployeeService.get_employees_by_position("worker")
    lg: ManagedListGroup = dialog_manager.find("lg")

    for slave in slaves:
        x: ManagedCheckbox = lg.find_for_item("sel_slaves", str(slave["userid"]))
        if x.is_checked():
            y: ManagedRadio = lg.find_for_item("prim_slave", str(slave["userid"]))
            user = (slave["userid"], y.get_checked())
            dialog_manager.dialog_data["task"]["slaves"].append(user)

    await next_or_end(callback, button, dialog_manager)


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
        return someone_task.get("taskid")

    def send_newtask_note(userid, task):
        scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
        if userid:
            scheduler.add_job(
                new_task,
                "interval",
                minutes=5,
                next_run_time=datetime.datetime.now(),
                args=[userid, task["title"], task["taskid"]],
                id=str(userid) + str(task["taskid"]),
                replace_existing=True,
            )

    recdata = {"dttm": datetime.datetime.now().replace(microsecond=0), "employee": None}
    data: dict = manager.dialog_data.get("task", {})
    data.setdefault("created", datetime.datetime.now().replace(microsecond=0))
    data.setdefault("creator", clb.from_user.id)
    operator = EmployeeService.get_employee(clb.from_user.id)

    if data.get("slaves") or data.get("slave"):
        data["status"] = "назначено"
    else:
        data["status"] = "открыто"
        data.setdefault("slaves", []).append((None, None))
    data.setdefault("status", "открыто")

    for i in (
        "entity",
        "agreement",
        "priority",
        "phone",
        "title",
        "description",
        "media_id",
        "media_type",
        "slave",
        "simple_report",
    ):
        data.setdefault(i, None)

    if is_exist(data):
        if data.get("slaves"):
            first = data.get("slaves", []).pop(0)
            data["slave"] = first[0]
            if first[1] == "пом":
                data["simple_report"] = 1

        task = dict(TaskService.update_task(data))
        send_newtask_note(data["slave"], task)
        recdata["task"] = task["taskid"]
        recdata["record"] = f'Заявку отредактировал {operator.get("username")}'
        JournalService.new_record(recdata)

        for slave in data.get("slaves", []):
            data["slave"] = slave[0]
            if slave[1] == "пом":
                data["simple_report"] = 1
            task = dict(TaskService.save_task(data))
            send_newtask_note(data["slave"], task)
            recdata["task"] = task.get("taskid")
            recdata["record"] = (
                f'заявку создал {EmployeeService.get_employee(task.get("creator")).get("username")}'
            )
            JournalService.new_record(recdata)

        scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
        job = scheduler.get_job(job_id="delay" + str(data["taskid"]))
        if job:
            job.remove()

        if data.get("return"):
            del data["return"]
            recdata["task"] = data["taskid"]
            recdata["record"] = f'Заявку вернул в работу {operator.get("username")}'
            JournalService.new_record(recdata)

        await clb.answer("Заявка отредактирована.", show_alert=True)

    else:
        for slave in data.get("slaves", []):
            data["slave"] = slave[0]
            if slave[1] == "пом":
                data["simple_report"] = 1
            task = dict(TaskService.save_task(data))
            send_newtask_note(data["slave"], task)

            recdata["task"] = task.get("taskid")
            recdata["record"] = (
                f'заявку создал {EmployeeService.get_employee(task.get("creator")).get("username")}'
            )
            JournalService.new_record(recdata)

        await clb.answer(
            "Заявка создана.",
            show_alert=True,
        )
        users = EmployeeService.get_employees_by_position("operator")
        userids = [user["userid"] for user in users]

        for userid in userids:
            send_newtask_note(userid, task)

    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


async def on_start(data, manager: DialogManager):
    manager.dialog_data["task"] = data or {}
    lg = manager.find("lg")
    users = EmployeeService.get_employees_by_position("worker")

    for user in users:
        chckbox: ManagedRadio = lg.find_for_item("prim_slave", str(user["userid"]))
        await chckbox.set_checked("пом")


async def on_return(clb: CallbackQuery, button, manager: DialogManager):
    task = manager.dialog_data.get("task", {})
    task["status"] = "в работе" if task["slave"] else "открыто"
    task["return"] = True

    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
    job = scheduler.get_job(str(task["taskid"]))
    if job:
        job.remove()

    await manager.start(state=states.NewSG.preview, data=task)

    # if task["slave"]:
    #     TaskService.change_status(taskid, "в работе")
    # else:
    #     TaskService.change_status(taskid, "открыто")

    # user = EmployeeService.get_employee(clb.from_user.id)
    #     "record": f'вернул в работу, {user.get("username")}',
    # }
    # JournalService.new_record(recdata)

    #     await clb.answer("Заявка возвращена в работу.", show_alert=True)
    # else:
    #     await clb.answer("Заявка уже в работе.", show_alert=True)


async def on_del_performer(clb: CallbackQuery, button, manager: DialogManager):
    manager.dialog_data["task"]["slave"] = None
    manager.dialog_data["task"]["username"] = None
    manager.dialog_data["task"]["slaves"] = list()
    await next_or_end(clb, button, manager)


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

    recdata = {
        "dttm": datetime.datetime.now().replace(microsecond=0),
        "task": manager.dialog_data.get("task", {}).get("taskid"),
        "employee": manager.dialog_data.get("task", {}).get("userid"),
        "record": f'принята в работу, {manager.dialog_data.get("task", {}).get("username")}',
    }
    JournalService.new_record(recdata)

    await callback.answer(
        f'Заявка {manager.dialog_data.get("task", {}).get("title")} принята в работу.'
    )
    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


async def on_perform(callback: CallbackQuery, button: Button, manager: DialogManager):
    data = manager.dialog_data.get("task", {})
    TaskService.change_status(data.get("taskid"), TasksStatuses.PERFORMING.value)
    data["performed_time"] = str(datetime.datetime.now().replace(microsecond=0))
    if data.get("simple_report"):
        await manager.start(prf_states.PrfPerformedSG.confirm, data=data)
    else:
        await manager.start(prf_states.PrfPerformedSG.pin_act, data=data)


async def get_back(callback: CallbackQuery, button: Button, manager: DialogManager):
    TaskService.change_status(
        manager.dialog_data.get("task", {}).get("taskid"), "в работе"
    )

    user = EmployeeService.get_employee(callback.from_user.id)
    recdata = {
        "dttm": datetime.datetime.now().replace(microsecond=0),
        "task": manager.dialog_data.get("task", {}).get("taskid"),
        "employee": manager.dialog_data.get("task", {}).get("userid"),
        "record": f'вернул в работу, {user.get("username")}',
    }
    JournalService.new_record(recdata)

    await callback.answer(
        f'Заявка {manager.dialog_data.get("task", {}).get("title")} снова в работе.'
    )


async def show_operator_media(callback: CallbackQuery, button, manager: DialogManager):
    mediatype = manager.dialog_data.get("task", {}).get("media_type")
    mediaid = manager.dialog_data.get("task", {}).get("media_id").split(",")
    await manager.start(
        state=states.MediaSG.main,
        data={"type": mediatype, "id": mediaid, "wintitle": "Медиа от оператора"},
    )


async def show_performer_media(callback: CallbackQuery, button, manager: DialogManager):
    mediaid = manager.dialog_data.get("task", {}).get("resultid").split(",")
    await manager.start(
        state=states.MediaSG.main,
        data={
            "type": ContentType.VIDEO,
            "id": mediaid,
            "wintitle": "Медиа от исполнителя",
        },
    )


async def show_act(callback: CallbackQuery, button, manager: DialogManager):
    mediaid = manager.dialog_data.get("task", {}).get("actid").split(",")
    await manager.start(
        state=states.MediaSG.main,
        data={"type": ContentType.PHOTO, "id": mediaid, "wintitle": "Акт"},
    )


async def on_close(callback: CallbackQuery, button, manager: DialogManager):
    await manager.start(
        state=OpCloseTaskSG.closing_choice,
        data=manager.dialog_data.get("task"),
    )


async def on_remove(callback: CallbackQuery, button, manager: DialogManager):
    await manager.start(state=OpRemoveTaskSG.main, data=manager.dialog_data.get("task"))


async def on_without_agreement(callback: CallbackQuery, button, manager: DialogManager):
    manager.dialog_data["task"]["agreement"] = None
    await next_or_end(callback, button, manager)


async def on_back(callback: CallbackQuery, button, manager: DialogManager):
    if manager.dialog_data.get("finished"):
        await manager.switch_to(state=states.NewSG.preview)
    else:
        await manager.back()


async def entity_search(message: Message, message_input, manager: DialogManager):
    manager.dialog_data["subentity"] = message.text or None
    await manager.next()


async def on_entity_fltr(
    callback: CallbackQuery, select, manager: DialogManager, entid: str, /
):
    manager.dialog_data["entid"] = entid
    await manager.next()


async def on_performer(
    callback: CallbackQuery, select, manager: DialogManager, userid: str, /
):
    manager.dialog_data["userid"] = userid
    await manager.next()


async def on_date(
    event: ChatEvent, widget, dialog_manager: DialogManager, date: datetime.date
):
    dialog_manager.dialog_data["date"] = date.strftime("%Y-%m-%d")
    await dialog_manager.next()


async def on_status(
    callback: CallbackQuery, select, manager: DialogManager, status: str, /
):
    manager.dialog_data["status"] = status
    await manager.start(state=states.TasksSG.tasks, data=manager.dialog_data)


async def filters_handler(callback: CallbackQuery, button, manager: DialogManager):
    await manager.start(state=states.TasksSG.tasks, data=manager.dialog_data)


async def reset_journal_page(callback: CallbackQuery, button, manager: DialogManager):
    await manager.find("scroll_taskjournal").set_page(0)
