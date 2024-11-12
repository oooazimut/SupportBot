from datetime import datetime

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from db.service import (
    car_service,
    employee_service,
    entity_service,
    journal_service,
    receipts_service,
)
from redis.asyncio.client import Redis

from . import states


async def on_location(
    callback: CallbackQuery, select, dialog_manager: DialogManager, location: str, /
):
    if not int(location):
        r = Redis()
        data = await r.get(str(callback.from_user.id))
        data = data.decode("utf-8")
        await r.aclose()
    else:
        data = entity_service.get_entity(location)["name"]

    dialog_manager.dialog_data["location"] = data
    await dialog_manager.switch_to(states.JrMainMenuSG.action)


async def on_action(
    callback: CallbackQuery, select, dialog_manager: DialogManager, action: str, /
):
    user = employee_service.get_employee(callback.from_user.id)
    last_record = journal_service.get_last_record(callback.from_user.id)
    current_record = f"{dialog_manager.dialog_data.get('location')} {action}"
    if last_record and action in last_record:
        await callback.answer(
            f"ПРЕДУПРЕЖДЕНИЕ!\nВ ПРЕДЫДУЩЕЙ ЗАПИСИ ТАКОЕ ЖЕ ДЕЙСТВИЕ!\nПредыдущая запись: {last_record}\nТекущая запись: {current_record}",
            show_alert=True,
        )

    dialog_manager.dialog_data["employee"] = user.get("userid")
    dialog_manager.dialog_data["task"] = None
    dialog_manager.dialog_data["record"] = current_record

    if (
        dialog_manager.dialog_data.get("location", "").lower() in ("дом", "офис")
        and action == "Уехал"
        and user["position"] == "worker"
    ):
        await dialog_manager.switch_to(states.JrMainMenuSG.sel_car)
    else:
        await dialog_manager.next()


async def on_confirm(callback: CallbackQuery, button, manager: DialogManager):
    journal_service.new_record(manager.dialog_data)

    if manager.dialog_data.get("current_car"):
        car_service.pin_car(manager.dialog_data["current_car"], callback.from_user.id)
        del manager.dialog_data["current_car"]

    if manager.dialog_data["record"].split()[-1] == "Уехал":
        r = Redis()
        await r.delete(str(callback.from_user.id))
        await r.aclose()

    await manager.done()
    await callback.answer("Запись сделана", show_alert=True)


async def object_input(message: Message, message_input, manager: DialogManager):
    manager.dialog_data["location"] = message.text

    r = Redis()
    await r.set(str(message.from_user.id), message.text)
    await r.aclose()

    await manager.next()


async def pin_receipt(message: Message, message_input, manager: DialogManager):
    dttm = datetime.now()
    employee = message.from_user.id
    receipt = message.photo[-1].file_id
    caption = message.caption

    receipts_service.new_receipt(
        {"dttm": dttm, "employee": employee, "receipt": receipt, "caption": caption}
    )
    await manager.done()


async def on_search(callback: CallbackQuery, button, manager: DialogManager):
    user = employee_service.get_employee(callback.from_user.id)
    data = {}

    if user.get("position") in ("worker",):
        data["userid"] = user.get("userid")

    await manager.start(states.JrSearchSG.datestamp, data=data)


async def on_checks(callback: CallbackQuery, button, manager: DialogManager):
    await manager.find("receipts_scroll").set_page(0)


async def on_car(
    callback: CallbackQuery, select, manager: DialogManager, car_id: str, /
):
    manager.dialog_data["current_car"] = car_id
    await manager.switch_to(states.JrMainMenuSG.confirm)
