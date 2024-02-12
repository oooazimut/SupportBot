from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from db import task_service


class TasksFactory(CallbackData):
    status: str
    taskid: int


async def assigned_handler(callback: CallbackQuery, button: Button, manager: DialogManager):
    kb = InlineKeyboardBuilder()
    tasks = task_service.get_tasks_by_status('назначено')
    if tasks:
        for task in tasks:
            kb.button(text=f'{task["title"]}\n{task["priority"]}', callback_data=TasksFactory(
                status=task['status'], taskid=task['id']))

    await callback.message.answer('sdfasdfsadf')


async def in_progress_handler(callback: CallbackQuery, button: Button, manager: DialogManager):
    # await callback.message.delete()
    await callback.answer('Вот так')


async def archive_handler(callback: CallbackQuery, button: Button, manager: DialogManager):
    # await callback.message.delete()
    await callback.answer('Вот так')
