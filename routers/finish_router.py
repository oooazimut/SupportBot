from aiogram import Router
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from routers.start_router import START_STATES
from supp_bot import empl_service

router = Router()


@router.message()
async def start_handler(message: Message, dialog_manager: DialogManager):
    print(message.from_user.id)
    print(message.from_user.full_name)
    user = empl_service.get_employee(userid=message.from_user.id)
    if user:
        status = user['status']
    else:
        status = 'customer'
    await dialog_manager.start(state=START_STATES[status], mode=StartMode.RESET_STACK)
