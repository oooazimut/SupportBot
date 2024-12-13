from datetime import datetime

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager

from config import TasksStatuses, TasksTitles
from db.service import customer_service, task_service
from jobs import handle_description
from notifications import new_customer_task_notification
from tasks import states as task_states

from . import states


async def on_new_task(callback: CallbackQuery, button, dialog_manager: DialogManager):
    if customer_service.get_one(callback.from_user.id):
        await dialog_manager.start(state=states.NewTaskSG.preview)
    else:
        await dialog_manager.start(states.NewCustomerSG.name)
        await callback.answer(
            "Чтобы можно было создавать заявки, нужно зарегистрироваться. Давайте сделаем это!",
            show_alert=True,
        )


async def on_current_tasks(
    callback: CallbackQuery, button, dialog_manager: DialogManager
):
    data = {
        "wintitle": TasksTitles.OPENED,
        "current": True,
    }
    customer = customer_service.get_one(callback.from_user.id) or {}
    if customer.get("object"):
        dict_update = {"entid": customer.get("object")}
    else:
        dict_update = {"creator": customer.get("id")}
    data.update(dict_update)

    await dialog_manager.start(state=task_states.TasksSG.tasks, data=data)


async def on_customer_archive(
    callback: CallbackQuery, button, dialog_manager: DialogManager
):
    data = {"wintitle": TasksTitles.ARCHIVE, "status": TasksStatuses.ARCHIVE}
    customer = customer_service.get_one(callback.from_user.id)
    if customer.get("object"):
        dict_update = {"entid": customer.get("object")}
    else:
        dict_update = {"creator": customer.get("id")}
    data.update(dict_update)
    await dialog_manager.start(state=task_states.TasksSG.tasks, data=data)


async def next_or_end(event, widget, dialog_manager: DialogManager, *_):
    if dialog_manager.dialog_data.get("finished"):
        await dialog_manager.switch_to(states.NewCustomerSG.preview)
    else:
        await dialog_manager.next()


async def on_confirm_customer_creating(
    callback: CallbackQuery, button, dialog_manager: DialogManager
):
    dialog_manager.dialog_data["customer"]["name"] += (
        f": {dialog_manager.dialog_data['customer']['object']}"
    )
    customer_service.new(**dialog_manager.dialog_data["customer"])
    await dialog_manager.done()
    await callback.answer(
        "Отлично, теперь вы можете создавать заявки!", show_alert=True
    )


async def description_handler(message: Message, message_input, manager: DialogManager):
    task = manager.dialog_data.setdefault("task", {})
    handle_description(message, task)


async def on_confirm_customer_task_creating(
    callback: CallbackQuery, button, dialog_manager: DialogManager
):
    customer = customer_service.get_one(callback.from_user.id)
    task: dict = dialog_manager.dialog_data.get("task", {})

    [task.setdefault(key, "") for key in ("description", "media_id", "media_type")]

    task.update(
        created=datetime.now().replace(microsecond=0),
        creator=customer.get("id"),
        phone=customer.get("phone"),
        entity=customer.get("object"),
        title=customer.get("name"),
        status=TasksStatuses.FROM_CUSTOMER,
    )
    task.update({
        key: None
        for key in (
            "priority",
            "act",
            "slave",
            "agreement",
            "simple_report",
            "recom_time",
        )
    })
    task_service.new(**task)
    await new_customer_task_notification(customer)
    await dialog_manager.done()
    await callback.answer(
        'Ваша заявка принята в работу. Статус заявки можно отслеживать в меню "Заявки"->"Открытые".',
        show_alert=True,
    )
