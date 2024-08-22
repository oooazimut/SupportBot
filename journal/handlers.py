from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from db.service import EmployeeService, JournalService

from . import states


async def on_location(
    callback: CallbackQuery, select, dialog_manager: DialogManager, location: str, /
):
    dialog_manager.dialog_data["location"] = location
    await dialog_manager.next()


async def on_action(
    callback: CallbackQuery, select, dialog_manager: DialogManager, action: str, /
):
    user = EmployeeService.get_employee(callback.from_user.id)

    dialog_manager.dialog_data["action"] = action
    dialog_manager.dialog_data["employee"] = user.get("userid")
    dialog_manager.dialog_data["task"] = None
    dialog_manager.dialog_data["record"] = (
        f'{user.get("username")} {dialog_manager.dialog_data.get("location")} {dialog_manager.dialog_data.get("action")}'
    )
    await dialog_manager.next()


async def on_confirm(callback: CallbackQuery, button, manager: DialogManager):
    JournalService.new_record(manager.dialog_data)
    await manager.done()
    await callback.answer("Запись сделана", show_alert=True)


async def on_search(callback: CallbackQuery, button, manager: DialogManager):
    user = EmployeeService.get_employee(callback.from_user.id)
    if user.get("position") in ("worker", ):
        await manager.start(
            states.JrSearchSG.datestamp, data={"userid": user.get("userid")}
        )
    else:
        await manager.start(states.JrSearchSG.user)
