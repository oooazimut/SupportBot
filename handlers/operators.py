import datetime
from typing import Any

from aiogram import Bot
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import empl_service
from db import task_service
from jobs import close_task
from states import WorkersSG, OpTaskSG, TaskCreating, PerformedTaskSG


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
    manager.dialog_data['task'] = task
    await manager.switch_to(OpTaskSG.preview)


async def on_addit(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(OpTaskSG.additional)


async def on_back_to_preview(callback, button, manager: DialogManager):
    await manager.switch_to(OpTaskSG.preview, show_mode=ShowMode.SEND)


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


async def go_addslaves(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(WorkersSG.add_slv)


async def insert_slaves(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    name = manager.find('user_name').get_value
    user_id = manager.find('user_id').get_value
    empl_service.insert_employee(name, user_id, 'worker')
    await callback_query.answer('Новый работник добавлен.', show_alert=True)
    await manager.done()


async def insert_operator(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    name = manager.find('user_name').get_value
    user_id = manager.find('user_id').get_value
    empl_service.insert_employee(name, user_id, 'operator')
    await callback_query.answer('Новый оператор добавлен.', show_alert=True)
    await manager.done()


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


class TaskCallbackFactory(CallbackData, prefix='return_task'):
    action: str
    taskid: int


async def on_close(callback: CallbackQuery, button: Button, manager: DialogManager):
    taskid = manager.start_data['taskid']
    user = manager.start_data['creator']
    run_date = datetime.datetime.now() + datetime.timedelta(days=3)
    scheduler: AsyncIOScheduler = manager.middleware_data['scheduler']
    bot: Bot = manager.middleware_data['bot']
    bg = manager.bg(user_id=user, chat_id=user)

    task_service.change_status(taskid, 'выполнено')
    scheduler.add_job(close_task, trigger='date', run_date=run_date, args=[taskid], id=str(taskid))
    await bg.start(state=PerformedTaskSG.main, data={'taskid': taskid})
    await manager.switch_to(OpTaskSG.tas)
