from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button

from db import task_service
from db.service import EntityService
from states import WorkerSG, WorkerTaskSG


async def on_assigned(callback: CallbackQuery, button: Button, manager: DialogManager):
    data = task_service.get_tasks_by_status('назначено', userid=callback.from_user.id)
    if data:
        manager.dialog_data[str(callback.from_user.id)] = data
        await manager.switch_to(WorkerSG.assigned)
    else:
        await callback.answer('Нет назначенных заявок')


async def on_progress(callback: CallbackQuery, button: Button, manager: DialogManager):
    data = []
    in_progress = task_service.get_tasks_by_status('в работе', userid=callback.from_user.id)
    performed = task_service.get_tasks_by_status('выполнено', userid=callback.from_user.id)
    if performed:
        for i in performed:
            i['priority'] += '\U00002705'
    data.extend(in_progress)
    data.extend(performed)
    if data:
        print(data)
        manager.dialog_data[str(callback.from_user.id)] = data
        await manager.switch_to(WorkerSG.in_progress)
    else:
        await callback.answer('Нет заявок в работе.')


async def on_archive(callback: CallbackQuery, button: Button, manager: DialogManager):
    data = task_service.get_tasks_by_status('закрыто', userid=callback.from_user.id)
    if data:
        manager.dialog_data[str(callback.from_user.id)] = data
        await manager.switch_to(WorkerSG.archive)
    else:
        await callback.answer('Архив пустой.')

async def on_object_task(callback: CallbackQuery, widget: Any, manager: DialogManager):
    await manager.switch_to(WorkerSG.entites_on_task)
async def next_dialog(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(WorkerSG.enter_dialog)
async def on_task(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    task = task_service.get_task(item_id)[0]
    await manager.start(WorkerTaskSG.main, data=task)

async def entites_name_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    entities = EntityService.get_entities_by_substr(message.text)
    if entities:
        manager.dialog_data['entities'] = entities
        print(entities)
    else:
        pass
async def tasks_for_entities(callback: CallbackQuery, widget: Any, manager: DialogManager):

    await manager.switch_to(WorkerSG.tasks_entities)