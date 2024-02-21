from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from db import task_service
from states import OperatorSG

async def on_task(callback_query: CallbackQuery, button:Button, manager: DialogManager):
