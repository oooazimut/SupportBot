from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from functions.db.get import get_employee
from states import OperatorSG, WorkerSG, CustomerSG

router = Router()

START_STATES = {
    'operator': OperatorSG.main,
    'worker': WorkerSG.main,
    'customer': CustomerSG.main
}


@router.message(CommandStart())
async def start_handler(message: Message, dialog_manager: DialogManager):
    userid = message.from_user.id
    try:
        status = get_employee(userid)['status']
    except TypeError:
        status = 'customer'
    print(status)
    await dialog_manager.start(state=START_STATES[status], mode=StartMode.RESET_STACK)
