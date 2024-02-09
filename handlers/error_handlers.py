from aiogram.types import ErrorEvent
from aiogram_dialog import DialogManager, StartMode

from config import START_STATES
from db import empl_service


async def ui_error_handler(event: ErrorEvent, dialog_manager: DialogManager):
    userid = dialog_manager.middleware_data['event_from_user'].id
    user = empl_service.get_employee(userid=userid)
    if user:
        status = user['status']
    else:
        status = 'customer'
    await dialog_manager.start(state=START_STATES[status], mode=StartMode.RESET_STACK)
