import operator

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Row, Select, Column, Button, SwitchTo, Cancel
from aiogram_dialog.widgets.text import Const, Format

from db import task_service
from handlers.worker_handlers import on_assigned, on_archive, on_progress, on_task
from states import WorkerSG, WorkerTaskSG


async def task_getter(dialog_manager: DialogManager, **kwargs):
    userid = str(dialog_manager.middleware_data['event_from_user'].id)
    tasks = dialog_manager.dialog_data[userid]
    return {'tasks': tasks}


main_dialog = Dialog(
    Window(
        Const('Главное меню:'),
        Row(
            Button(Const('Назначенные'), id='worker_assigned', on_click=on_assigned),
            Button(Const('В работе'), id='worker_in_progress', on_click=on_progress),
            Button(Const('Архив'), id='worker_archive', on_click=on_archive),
        ),
        state=WorkerSG.main
    ),
    Window(
        Const('Назначенные заявки'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='worker_assigned_tasks',
                item_id_getter=operator.itemgetter('id'),
                items='tasks',
                on_click=on_task

            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=WorkerSG.main),
        state=WorkerSG.assigned,
        getter=task_getter
    ),
    Window(
        Const('Заявки в работе:'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='worker_in_progress_tasks',
                item_id_getter=operator.itemgetter('id'),
                items='tasks',
                on_click=on_task
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=WorkerSG.main),
        state=WorkerSG.in_progress,
        getter=task_getter
    ),
    Window(
        Const('Архив заявок:'),
        Column(
            Select(
                Format('{item[title]}'),
                id='worker_archive_tasks',
                item_id_getter=operator.itemgetter('id'),
                items='tasks',
                on_click=on_task
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=WorkerSG.main),
        state=WorkerSG.archive,
        getter=task_getter
    )
)


async def accept_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    task_service.change_status(manager.start_data['id'], 'в работе')
    await callback.answer(f'Заявка {manager.start_data["title"]} принята в работу.')


async def refuse_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    task_service.change_status(manager.start_data['id'], 'открыто')
    await callback.answer(f'Вы отказались от заявки:  {manager.start_data["title"]}')


async def close_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    task_service.change_status(manager.start_data['id'], 'выполнено')
    await callback.answer(f'Заявка {manager.start_data["title"]} выполнена. Ожидаем потверждения от клиента.')


async def get_back(callback: CallbackQuery, button: Button, manager: DialogManager):
    task_service.change_status(manager.start_data['id'], 'в работе')
    await callback.answer(f'Заявка {manager.start_data["title"]} снова в работе.')

async def client_info(callback: CallbackQuery, button: Button, manager: DialogManager):
    pass



def is_opened(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'назначено'


def not_in_archive(data, widget, manager: DialogManager):
    return manager.start_data['status'] != 'закрыто'


def is_performed(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'выполнено'


def is_in_progress(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'в работе'


task_dialog = Dialog(
    Window(
        Format('{start_data[created]}'),
        Format('{start_data[name]}'),
        Format('{start_data[title]}'),
        Format('{start_data[description]}'),
        Format('Приоритет: {start_data[priority]}'),
        Format('Статус: {start_data[status]}'),
        Button(Const('Инфо от клиента'), id='client_task', on_click=client_info),
        Button(Const('Принять'), id='accept_task', on_click=accept_task, when=is_opened),
        Button(Const('Отказаться'), id='refuse_task', on_click=refuse_task, when=not_in_archive),
        Button(Const('Закрыть'), id='close_task', on_click=close_task, when=is_in_progress),
        Button(Const('Вернуть в работу'), id='back_to_work', on_click=get_back, when=is_performed),
        Cancel(Const('Назад')),
        state=WorkerTaskSG.main
    )
)
