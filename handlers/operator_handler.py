from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from db import task_service, empl_service
from db import task_service
from states import OperatorSG, TaskSG, WorkersSG


#Хендлеры для тасков
async def go_task(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(OperatorSG.tas)
async def go_slaves(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(OperatorSG.worker)
async def go_new_task(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    data = task_service.get_tasks_by_status('открытая')
    if data:
        await manager.switch_to(TaskSG.new_task)
    else:
        await callback_query.message.answer('Нет новых заявок')
        await callback_query.message.delete()

async def go_work_task(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    data = task_service.get_tasks_by_status('в работе')
    if data:
        await manager.switch_to(TaskSG.progress_task)
    else:
        await callback_query.message.answer('Нет заявок в работе')
        await callback_query.message.delete()
async def progress_task_getter(dialog_manager: DialogManager, **kwargs):
    data = task_service.get_tasks_by_status('в работе')
    tasks = task_service.get_tasks_by_status('выполнено')
    for  item in tasks:
        if item['status'] == 'выполнено':
            item['priority'] += '\U00002705'
    data.extend(tasks)
    return {'tasks': tasks}
async def go_archive(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    data = task_service.get_tasks_by_status('закрыто')
    if data:
        await manager.switch_to(TaskSG.archive_task)
    else:
        await callback_query.message.answer('Архив пустой.')
        await callback_query.message.delete()
async def archive_getter(dialog_manager: DialogManager, **kwargs):
    tasks = task_service.get_tasks_by_status('закрыто')
    return {'tasks': tasks}

async def on_task(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    task = task_service.get_task(item_id)[0]
    await manager.start(TaskSG.main, data=task)


#Хендлеры для сотрудников
async def go_operator(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(WorkersSG.opr)

async def go_worker(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(WorkersSG.slv)

async def operator_getter(dialog_manager: DialogManager, **kwargs):
    un = empl_service.get_employee("operator")
    return {'un': un}

async def worker_getter(dialog_manager: DialogManager, **kwargs):
    un = empl_service.get_employee("worker")
    return {'un': un}

#Хендлеры для обработки заявок
async def client_info(callback: CallbackQuery, button: Button, manager: DialogManager):
    pass

async def edit_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    pass
async def appoint_task(callback: CallbackQuery, button: Button, manager: DialogManager):

    pass

async def close_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    pass
async def get_back(callback: CallbackQuery, button: Button, manager: DialogManager):
    pass
async def create_task(callback: CallbackQuery, button: Button, manager: DialogManager):

    pass
