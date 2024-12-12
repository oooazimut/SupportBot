import datetime
import logging
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
from apscheduler.schedulers.asyncio import AsyncIOScheduler, asyncio
from config import TasksStatuses
from custom.bot import MyBot
from db.service import employee_service, entity_service, journal_service, task_service
from jobs import handle_description
from notifications import check_work_execution, new_task_notification
from operators.states import OpCloseTaskSG, OpDelayingSG, OpRemoveTaskSG
from performers import states as prf_states

from . import states

logger = logging.getLogger(__name__)


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
    entity = entity_service.get_one(ent_id)
    dialog_manager.dialog_data["task"].update(
        entity=entity["ent_id"],
        name=entity["name"],
    )
    await next_or_end(event, select, dialog_manager)


async def on_slave_choice(callback, button, dialog_manager: DialogManager):
    dialog_manager.dialog_data["task"]["slaves"] = list()
    slaves = employee_service.get_by_filters(position="worker")
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
    message: Message, message_input, manager: DialogManager
):
    task: dict = manager.dialog_data.get("task", {})
    handle_description(message, task)


async def ent_name_handler(
    message: Message, message_input: MessageInput, manager: DialogManager
):
    manager.dialog_data["subentity"] = message.text
    await manager.next()


async def on_confirm(clb: CallbackQuery, button: Button, manager: DialogManager):
    def is_exist(someone_task: dict):
        return someone_task.get("taskid")

    async def group_new_tasks(data: dict) -> dict:
        if not data.get("slaves"):
            return {}

        performers = data.get('slaves', [])
        task_keys = task_service.get_keys()
        data = {key: value for key, value in data.items() if key in task_keys}
        
        for user, role in performers:
            data.update(slave=user)
            if role == "пом":
                data["simple_report"] = 1
            else:
                data["simple_report"] = None

            task = task_service.new(**data)
            await new_task_notification([task["slave"]], task["title"], task["taskid"])

            recdata["task"] = task.get("taskid")
            recdata["record"] = (
                f"заявку создал {employee_service.get_one(task.get('creator')).get('username')}"
            )
            journal_service.new(**recdata)
        return task or {}

    current_dttm = datetime.datetime.now().replace(microsecond=0)
    recdata = {"dttm": current_dttm, "employee": None}
    data: dict = manager.dialog_data.get("task", {})
    data["created"] = current_dttm
    data.setdefault("creator", clb.from_user.id)
    operator = employee_service.get_one(clb.from_user.id)

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
            else:
                data["simple_report"] = None
        task_keys = task_service.get_keys()
        data = {key: value for key, value in data.items() if key in task_keys}
        task = task_service.update(**data)
        await new_task_notification([task["slave"]], task["title"], task["taskid"])

        recdata.update(
            task=task.get("taskid"),
            record=f"Заявку отредактировал {operator.get('username')}",
        )
        journal_service.new(**recdata)

        await group_new_tasks(data)

        scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
        job = scheduler.get_job(job_id="delay" + str(data["taskid"]))
        if job:
            job.remove()

        if data.get("return"):
            del data["return"]
            recdata["task"] = data["taskid"]
            recdata["record"] = f"Заявку вернул в работу {operator.get('username')}"
            journal_service.new(**recdata)

        await clb.answer("Заявка отредактирована.", show_alert=True)

    else:
        task: dict = await group_new_tasks(data)
        await clb.answer(
            "Заявка создана.",
            show_alert=True,
        )
        userids = [
            user["userid"]
            for user in employee_service.get_by_filters(position="operator")
        ]

        await new_task_notification(
            userids, task.get("title", ""), task.get("taskid", "")
        )

    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


async def on_start(data, manager: DialogManager):
    manager.dialog_data["task"] = data or {}
    lg = manager.find("lg")
    users = employee_service.get_by_filters(position="worker")

    for user in users:
        chckbox: ManagedRadio = lg.find_for_item("prim_slave", str(user["userid"]))
        await chckbox.set_checked("пом")


async def on_return(clb: CallbackQuery, button, manager: DialogManager):
    task = manager.dialog_data.get("task", {})
    task["status"] = "в работе" if task["slave"] else "открыто"
    task["return"] = True
    await manager.start(state=states.NewSG.preview, data=task)

    # if task["slave"]:
    #     task_service.change_status(taskid, "в работе")
    # else:
    #     task_service.change_status(taskid, "открыто")

    # user = employee_service.get_employee(clb.from_user.id)
    #     "record": f'вернул в работу, {user.get("username")}',
    # }
    # journal_service.new_record(recdata)

    #     await clb.answer("Заявка возвращена в работу.", show_alert=True)
    # else:
    #     await clb.answer("Заявка уже в работе.", show_alert=True)


async def on_del_performer(clb: CallbackQuery, button, manager: DialogManager):
    manager.dialog_data["task"]["slave"] = None
    manager.dialog_data["task"]["username"] = None
    manager.dialog_data["task"]["slaves"] = list()
    await next_or_end(clb, button, manager)


async def accept_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    task = manager.dialog_data.get("task", {})
    agreement = task.get("agreement")
    if agreement:
        await callback.answer(f"Требуется согласование c {agreement}!", show_alert=True)
        bot: Bot = MyBot.get_instance()
        operators: list = employee_service.get_by_filters(position="operator")
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Хорошо", callback_data="agr_not_is_readed")
        content = Text(
            Bold(
                f"{agreement} нужно согласование с {task.get('username')} по заявке {task.get('title')}!"
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

    task_service.update(
        taskid=manager.dialog_data.get("task", {}).get("taskid"),
        status=TasksStatuses.AT_WORK,
    )

    recdata = {
        "dttm": datetime.datetime.now().replace(microsecond=0),
        "task": manager.dialog_data.get("task", {}).get("taskid"),
        "employee": manager.dialog_data.get("task", {}).get("userid"),
        "record": f"принята в работу, {manager.dialog_data.get('task', {}).get('username')}",
    }
    journal_service.new(**recdata)

    await callback.answer(
        f"Заявка {manager.dialog_data.get('task', {}).get('title')} принята в работу."
    )
    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


async def on_perform(callback: CallbackQuery, button: Button, manager: DialogManager):
    data = manager.dialog_data.get("task", {})
    last_record = journal_service.get_last_record(callback.from_user.id)

    if (
        data.get("name")
        and "Уехал" in last_record
        and data.get("name") not in last_record
    ):
        await callback.answer(
            "Вы не сделали запись о прибытии на объект.", show_alert=True
        )
        return

    task_service.update(taskid=data.get("taskid"), status=TasksStatuses.PERFORMING)
    data["performed_time"] = str(datetime.datetime.now().replace(microsecond=0))
    if data.get("simple_report"):
        await manager.start(prf_states.PrfPerformedSG.confirm, data=data)
    else:
        if data.get("act"):
            await manager.start(prf_states.PrfPerformedSG.pin_act, data=data)
        else:
            await manager.start(prf_states.PrfPerformedSG.pin_videoreport, data=data)


async def get_back(callback: CallbackQuery, button: Button, manager: DialogManager):
    task_service.update(
        taskid=manager.dialog_data.get("task", {}).get("taskid"),
        status=TasksStatuses.AT_WORK,
    )

    user = employee_service.get_one(callback.from_user.id)
    recdata = {
        "dttm": datetime.datetime.now().replace(microsecond=0),
        "task": manager.dialog_data.get("task", {}).get("taskid"),
        "employee": manager.dialog_data.get("task", {}).get("userid"),
        "record": f"вернул в работу, {user.get('username')}",
    }
    journal_service.new(**recdata)

    await callback.answer(
        f"Заявка {manager.dialog_data.get('task', {}).get('title')} снова в работе."
    )


async def show_operator_media(callback: CallbackQuery, button, manager: DialogManager):
    task: dict = manager.dialog_data.get("task", {})
    data = dict(
        type=task.get("media_type", ""),
        id=task.get("media_id", ""),
        wintitle="Медиаданные",
    )
    await manager.start(
        state=states.MediaSG.main,
        data=data,
    )


async def show_performer_media(callback: CallbackQuery, button, manager: DialogManager):
    data = dict(
        type=ContentType.VIDEO,
        id=manager.dialog_data.get("task", {}).get("resultid", ""),
        wintitle="Видеотчеты исполнителя",
    )
    await manager.start(state=states.MediaSG.main, data=data)


async def show_act(callback: CallbackQuery, button, manager: DialogManager):
    data = dict(
        type=ContentType.PHOTO,
        id=manager.dialog_data.get("task", {}).get("actid", ""),
        wintitle="Акт",
    )
    await manager.start(state=states.MediaSG.main, data=data)


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


async def add_description(message: Message, message_input, manager: DialogManager):
    task = manager.dialog_data.get("task", {})
    handle_description(message, task)
    task_service.update(**task)
    messg = await message.answer("Медиа добавлено")
    await manager.switch_to(states.TasksSG.task)
    await asyncio.sleep(1)
    await messg.delete()


async def on_arrived(callback: CallbackQuery, button, manager: DialogManager):
    last_record = journal_service.get_last_record(callback.from_user.id)
    if "Приехал" in last_record:
        await callback.answer(
            f"Нет записи о том, что вы покинули предыдущий объект ({last_record.rsplit(maxsplit=1)[0]})!",
            show_alert=True,
        )
    else:
        await manager.switch_to(states.TasksSG.confirm_arrived)


async def confirm_arrived(callback: CallbackQuery, button, manager: DialogManager):
    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
    run_time = datetime.datetime.now() + datetime.timedelta(minutes=30)
    record = f"{manager.dialog_data.get('task', {}).get('name')} Приехал"
    data = dict(
        employee=callback.from_user.id,
        task=manager.dialog_data.get("task", {}).get("taskid"),
        record=record,
    )

    journal_service.new(**data)
    await callback.answer(
        f"Запись о прибытии на объект {manager.dialog_data.get('task', {}).get('name')} добавлена",
        show_alert=True,
    )
    scheduler.add_job(
        check_work_execution,
        trigger="date",
        run_date=run_time,
        args=[callback.from_user.id],
    )
    await manager.switch_to(
        state=states.TasksSG.task, show_mode=ShowMode.DELETE_AND_SEND
    )


async def on_clone(callback: CallbackQuery, button, manager: DialogManager):
    taskid = manager.dialog_data.get("task", {}).get("taskid")
    task_service.clone_task(taskid)
    await callback.answer("Заявка клонирована", show_alert=True)
