from typing import Any

from aiogram import types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from db import empl_service
from db import task_service
from states import TaskSG, WorkersSG, OpTaskSG


# Хендлеры для тасков
async def go_task(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(OpTaskSG.tas)


async def go_slaves(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(WorkersSG.main)


async def go_new_task(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    data = task_service.get_tasks_by_status('открытая')
    if data:
        await manager.switch_to(OpTaskSG.new_task)
    else:
        await callback_query.answer('Нет новых заявок', show_alert=True)


async def go_work_task(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    data = task_service.get_tasks_by_status('в работе')
    confirmed = task_service.get_tasks_by_status('выполнено')
    data.extend(confirmed)
    if data:
        await manager.switch_to(OpTaskSG.progress_task)
    else:
        await callback_query.answer('Нет заявок в работе', show_alert=True)


async def progress_task_getter(dialog_manager: DialogManager, **kwargs):
    data = task_service.get_tasks_by_status('в работе')
    tasks = task_service.get_tasks_by_status('выполнено')
    for item in tasks:
        if item['status'] == 'выполнено':
            item['priority'] += '\U00002705'
    data.extend(tasks)
    return {'tasks': data}


async def go_archive(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    data = task_service.get_tasks_by_status('закрыто')
    if data:
        await manager.switch_to(OpTaskSG.archive_task)
    else:
        await callback_query.answer('Архив пустой.', show_alert=True)


async def archive_getter(dialog_manager: DialogManager, **kwargs):
    tasks = task_service.get_tasks_by_status('закрыто')
    return {'tasks': tasks}


async def on_task(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    task = task_service.get_task(item_id)[0]
    await manager.start(TaskSG.main, data=task)


# Хендлеры для сотрудников
async def go_operator(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(WorkersSG.opr)


async def go_worker(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(WorkersSG.slv)


async def operator_getter(dialog_manager: DialogManager, **kwargs):
    un = empl_service.get_employee("operator")
    return {'un': un}


async def worker_getter(dialog_manager: DialogManager, **kwargs):
    un = empl_service.get_employees("worker")
    return {'un': un}


async def client_info(callback: CallbackQuery, button: Button, manager: DialogManager):
    pass


async def edit_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    pass


async def appoint_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(OpTaskSG.tas)


async def set_workers(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    task_service.change_worker(manager.start_data['id'], item_id[0])
    bot = manager.middleware_data['bot']
    await bot.send_message(item_id[0], 'Вам назначена задача')
    await manager.switch_to(OpTaskSG.new_task)


async def close_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    task_service.change_status(manager.start_data['id'], 'выполнено')
    bot = manager.middleware_data['bot']
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text='Подтвердить выполнение',
        callback_data='confirm_task'
    ))
    await bot.send_message(manager.start_data['creator'], 'Ваша заявка выполнена, проверьте как она выполнена',
                           replay_markup=builder.as_markup())
    await manager.done()


async def create_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    pass
