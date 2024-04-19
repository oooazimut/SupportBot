from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import empl_service
from db import task_service
from states import WorkersSG, OpTaskSG, TaskCreating


# Хендлеры для тасков
async def go_task(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(OpTaskSG.tas)


async def go_slaves(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(WorkersSG.main)


async def on_tasks(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    tasks = list()
    new_tasks = task_service.get_tasks_by_status('открыто')
    confirmed_tasks = task_service.get_tasks_by_status('выполнено')
    assigned_tasks = sorted(
        task_service.get_tasks_by_status('назначено'),
        key=lambda x: x['priority'] if x['priority'] else ''
    )
    for item in (assigned_tasks, new_tasks, confirmed_tasks):
        tasks.extend(item)
    if tasks:
        manager.dialog_data['tasks'] = tasks
        await manager.switch_to(OpTaskSG.opened_tasks)
    else:
        await callback_query.answer('Тут ничего нет.', show_alert=True)


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
    task = task_service.get_task(taskid=item_id)[0]
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
        un = dialog_manager.start_data['workers']
    return {'un': un}


async def edit_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(TaskCreating.preview, data=manager.dialog_data['task'])


async def on_close(callback: CallbackQuery, button: Button, manager: DialogManager):
    taskid = manager.dialog_data['task']['taskid']
    scheduler: AsyncIOScheduler = manager.middleware_data['scheduler']
    task_service.change_status(taskid, 'закрыто')
    job = scheduler.get_job(job_id=str(taskid))
    if job:
        job.remove()
        await callback.answer('Заявка перемещена в архив.', show_alert=True)
    else:
        await callback.answer('Заявка уже в архиве.', show_alert=True)
    await manager.switch_to(OpTaskSG.opened_tasks)


async def on_return(clb: CallbackQuery, button, manager: DialogManager):
    task = manager.dialog_data['task']
    task_service.change_status(task['taskid'], 'в работе')

    scheduler: AsyncIOScheduler = manager.middleware_data['scheduler']
    job = scheduler.get_job(str(task['taskid']))
    if job:
        job.remove()
        await clb.answer('Заявка возвращена в работу.', show_alert=True)
    else:
        await clb.answer('Заявка уже в работе.', show_alert=True)

    await manager.switch_to(OpTaskSG.opened_tasks)
