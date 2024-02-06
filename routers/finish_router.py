from aiogram import Router
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from functions.db.get import get_employee
from routers.start_router import START_STATES

router = Router()


@router.message()
async def start_handler(message: Message, dialog_manager: DialogManager):
    userid = message.from_user.id
    print(userid)
    try:
        status = get_employee(userid)['status']
    except TypeError:
        status = 'customer'
    print(status)
    await dialog_manager.start(state=START_STATES[status], mode=StartMode.RESET_STACK)
