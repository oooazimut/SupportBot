from typing import Any

from aiogram import types
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button

from db import empl_service
from db import task_service
from states import TaskSG, WorkersSG, OpTaskSG, WorkerSendSG, TaskCreating


# Хендлеры для тасков
async def go_task(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(OpTaskSG.tas)


async def go_slaves(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(WorkersSG.main)


async def go_new_task(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    data = task_service.get_tasks_by_status('открыто')
    if data:
        manager.dialog_data['tasks'] = data
        await manager.switch_to(OpTaskSG.new_task)
    else:
        await callback_query.answer('Нет новых заявок', show_alert=True)


async def go_work_task(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    data = task_service.get_tasks_by_status('в работе')
    assigned = task_service.get_tasks_by_status('назначено')
    if assigned:
        for item in assigned:
            item['emoji'] = '\U00002753'
        data.extend(assigned)
    confirmed = task_service.get_tasks_by_status('выполнено')
    if confirmed:
        for item in confirmed:
            item['emoji'] = '\U00002705'
        data.extend(confirmed)
    if data:
        manager.dialog_data['tasks'] = data
        await manager.switch_to(OpTaskSG.progress_task)
    else:
        await callback_query.answer('Нет заявок в работе', show_alert=True)


async def tasks_getter(dialog_manager: DialogManager, **kwargs):
    tasks = dialog_manager.dialog_data['tasks']
    return {'tasks': tasks}


async def go_archive(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    data = task_service.get_tasks_by_status('закрыто')
    if data:
        manager.dialog_data['tasks'] = data
        await manager.switch_to(OpTaskSG.archive_task)
    else:
        await callback_query.answer('Архив пустой.', show_alert=True)


async def on_task(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    task = next((t for t in manager.dialog_data['tasks'] if t['taskid'] == int(item_id)), None)
    manager.dialog_data['taskid'] = item_id
    await manager.start(TaskSG.main, data=task)


# Хендлеры для сотрудников
async def go_operator(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    operators = empl_service.get_employees_by_position('operator')
    if operators:
        manager.dialog_data['operators'] = operators
        await manager.switch_to(WorkersSG.opr)
    else:
        await callback_query.answer('Операторы отсутствуют.', show_alert=True)


async def go_worker(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    workers = empl_service.get_employees_by_position('worker')
    if workers:
        manager.dialog_data['workers'] = workers
        await manager.switch_to(WorkersSG.slv)
    else:
        await callback_query.answer('Работники отсутствуют.', show_alert=True)


async def operator_getter(dialog_manager: DialogManager, **kwargs):
    un = dialog_manager.dialog_data['operators']
    return {'un': un}


async def worker_getter(dialog_manager: DialogManager, **kwargs):
    try:
        un = dialog_manager.dialog_data['workers']
    except KeyError:
        print(dialog_manager.start_data['workers'])
        un = dialog_manager.start_data['workers']
    return {'un': un}


async def client_info(callback: CallbackQuery, button: Button, manager: DialogManager):
    pass


async def edit_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(TaskCreating.preview, data=manager.start_data)


async def appoint_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    workers = empl_service.get_employees_by_position('worker')
    if workers:
        await manager.start(WorkerSendSG.set_worker, data={'workers': workers, 'task': manager.start_data})
    else:
        await callback.answer('Работников нет.', show_alert=True)


async def set_workers(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    print(item_id, manager.start_data['task']['taskid'])
    task_service.change_worker(task_id=manager.start_data['task']['taskid'], slave=item_id)
    bot = manager.middleware_data['bot']
    await bot.send_message(item_id, 'Вам назначена задача')
    await manager.done()


async def close_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    task_service.change_status(manager.start_data['taskid'], 'выполнено')
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
