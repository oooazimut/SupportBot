from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from db import task_service, empl_service
from db import task_service
from states import OperatorSG


#Хендлеры для тасков
async def go_task(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(OperatorSG.tas)
async def go_slaves(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(OperatorSG.slv)
async def go_new_task(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    data = task_service.get_tasks_by_status('открытая')
    if data:
        await manager.switch_to(OperatorSG.new_task)
    else:
        await callback_query.message.answer('Нет новых заявок')
        await callback_query.message.delete()
async def go_inw_task(dialog_manager: DialogManager, **kwargs):
    data = task_service.get_tasks_by_status('в работе')
    tasks = task_service.get_tasks_by_status('выполнено')
    for  item in tasks:
        if item['status'] == 'выполнено':
            item['priority'] += '\U00002705'
    data.extend(tasks)
    return {'tasks': tasks}

async def go_archive(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    tasks = task_service.get_tasks_by_status('закрыто')
    return {'tasks': tasks}


#Хендлеры для сотрудников
async def go_operator(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(OperatorSG.opr)

async def go_worker(callback_query: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(OperatorSG.slv)

async def operator_getter(dialog_manager: DialogManager, **kwargs):
    un = empl_service.get_employee("operator")
    return {'un': un}

async def worker_getter(dialog_manager: DialogManager, **kwargs):
    un = empl_service.get_employee("worker")
    return {'un': un}

async def on_confirm(clb: CallbackQuery, button: Button, manager: DialogManager):
    username = manager.find('worker_name_input').get_value()
    userid = manager.find('worker_id_input').get_value()
    empl_service.save_employee()