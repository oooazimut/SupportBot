from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from db import task_service
from states import WorkerSG


async def on_assigned(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    data = task_service.get_tasks_by_status('назначено', userid=callback_query.from_user.id)
    if data:
        await manager.switch_to(WorkerSG.assigned)
    else:
        await callback_query.message.answer('Нет назначенных заявок')
        await callback_query.message.delete()


async def on_progress(callback: CallbackQuery, button: Button, manager: DialogManager):
    in_progress = task_service.get_tasks_by_status('в работе', userid=callback.from_user.id)
    performed = task_service.get_tasks_by_status('выполнено', userid=callback.from_user.id)
    if in_progress or performed:
        await manager.switch_to(WorkerSG.in_progress)
    else:
        await callback.message.answer('Нет заявок в работе.')
        await callback.message.delete()


async def on_archive(callback: CallbackQuery, button: Button, manager: DialogManager):
    data = task_service.get_tasks_by_status('закрыто', userid=callback.from_user.id)
    if data:
        await manager.switch_to(WorkerSG.archive)
    else:
        await callback.message.answer('Архив пустой.')
        await callback.message.delete()

