from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from config import START_STATES
from db import empl_service, task_service

from pyrogram.types import CallbackQuery

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, dialog_manager: DialogManager):
    print(message.from_user.id)
    print(message.from_user.full_name)
    user = empl_service.get_employee(userid=message.from_user.id)
    if user:
        status = user['status']
    else:
        status = 'customer'
    await dialog_manager.start(state=START_STATES[status], mode=StartMode.RESET_STACK)
@router.callback_query(F.data == "confirm_task")
async def confirm_task(callback: CallbackQuery, dialog_manager: DialogManager):
    task_service.change_task_status(dialog_manager.start_data['id'], 'выполнено')
    await callback.message.delete()