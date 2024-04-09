from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, StartMode

from config import START_STATES
from db import empl_service, task_service
from handlers.operators import TaskCallbackFactory

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, dialog_manager: DialogManager):

    bot = dialog_manager.middleware_data['bot']
    txt = f'Пользователь {message.from_user.full_name} {message.from_user.id} запустил бота'
    await bot.send_message(chat_id=5963726977, text=txt)

    user = empl_service.get_employee(userid=message.from_user.id)
    if user:
        position = user['position']
    else:
        position = 'customer'
    await dialog_manager.start(state=START_STATES[position], mode=StartMode.RESET_STACK)
