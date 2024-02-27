from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from config import START_STATES
from db import empl_service

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, dialog_manager: DialogManager):

    bot = dialog_manager.middleware_data['bot']
    txt = f'Пользователь {message.from_user.full_name} {message.from_user.id} запустил бота'
    await bot.send_message(chat_id=5963726977, text=txt)

    user = empl_service.get_employee(userid=message.from_user.id)
    if user:
        status = user['status']
    else:
        status = 'customer'
    await dialog_manager.start(state=START_STATES[status], mode=StartMode.RESET_STACK)
