from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
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
    data.extend(in_progress)
    data.extend(performed)
    if data:
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


async def on_task(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    task = task_service.get_task(item_id)[0]
    await manager.start(WorkerTaskSG.main, data=task)


async def entites_name_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    entities = EntityService.get_entities_by_substr(message.text)
    if entities:
        manager.dialog_data['entities'] = entities
        await manager.switch_to(WorkerSG.enter_object)
    else:
        pass


async def on_entity(callback: CallbackQuery, select, manager: DialogManager, data, /):
    tasks = EntityService.get_task_for_entity(data)
    if tasks:
        manager.dialog_data['tasks'] = tasks
        await manager.switch_to(WorkerSG.tasks_entities)
    else:
        await callback.answer('Нет заявок на объекте!')


async def open_tasks(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    task = task_service.get_task(item_id)[0]
    await manager.start(WorkerTaskSG.main, data=task)


async def back_to_main(callback, button, manager: DialogManager):
    await manager.switch_to(WorkerSG.main, show_mode=ShowMode.DELETE_AND_SEND)


async def to_entities(callback, button, manager: DialogManager):
    await manager.switch_to(WorkerSG.entities_search, show_mode=ShowMode.DELETE_AND_SEND)


async def on_cancel(callback, button, manager: DialogManager):
    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


async def act_handler(msg: Message, widget: MessageInput, manager: DialogManager):
    actid = None
    acttype = msg.content_type
    match acttype:
        case 'document':
            actid = msg.document.file_id
        case 'photo':
            actid = msg.photo[-1].file_id

    data = {
        'taskid': manager.start_data['taskid'],
        'actid': actid,
        'acttype': acttype
    }

    task_service.add_act(data)
    await manager.switch_to(WorkerTaskSG.media_pin)
