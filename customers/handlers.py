from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager

from db.service import customer_service
from tasks import states as task_states
from . import states


async def on_new_task(callback: CallbackQuery, button, dialog_manager: DialogManager):
    if customer_service.get_customer(callback.from_user.id):
        await dialog_manager.start(state=task_states.NewSG.title)
    else:
        await dialog_manager.start(states.NewCustomerSG.name)


async def next_or_end(event, widget, dialog_manager: DialogManager, *_):
    if dialog_manager.dialog_data.get("finished"):
        await dialog_manager.switch_to(states.NewCustomerSG.preview)
    else:
        await dialog_manager.next()
