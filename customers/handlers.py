from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from db.service import customer_service

from . import states


async def on_new_task(callback: CallbackQuery, button, dialog_manager: DialogManager):
    if customer_service.get_customer(callback.from_user.id):
        await dialog_manager.start(state=states.NewTaskSG.preview)
    else:
        await dialog_manager.start(states.NewCustomerSG.name)
        await callback.answer(
            "Чтобы можно было создавать заявки, нужно зарегистрироваться. Давайте сделаем это!",
            show_alert=True,
        )


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
    customer_service.new_customer(**dialog_manager.dialog_data["customer"])
    await dialog_manager.done()
    await callback.answer(
        "Отлично, теперь вы можете создавать заявки!", show_alert=True
    )


async def on_confirm_customer_task_creating(
    callback: CallbackQuery, button, dialog_manager: DialogManager
):
    pass


async def description_handler(message: Message, message_input, manager: DialogManager):
    manager.dialog_data.setdefault("task", {}).setdefault("description", []).append(message.text)
    await manager.back()


async def video_handler(message: Message, message_input, manager: DialogManager):
    manager.dialog_data.get("task", {}).get("media_type", []).append(
        message.content_type
    )
    manager.dialog_data.get("task", {}).get("media_id", []).append(
        message.video.file_id
    )
    await manager.switch_to(state=states.NewTaskSG.preview)
