import operator

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Row, Select, Column, Button, SwitchTo
from aiogram_dialog.widgets.text import Const, Format

from db import task_service
from handlers.worker_handlers import on_assigned, on_archive, on_progress, on_assigned_task
from states import WorkerSG


async def assigned_getter(dialog_manager: DialogManager, **kwargs):
    userid = dialog_manager.middleware_data['event_from_user'].id
    tasks = task_service.get_tasks_by_status('назначено', userid=userid)
    return {'tasks': tasks}


async def in_progress_getter(dialog_manager: DialogManager, **kwargs):
    userid = dialog_manager.middleware_data['event_from_user'].id
    tasks = task_service.get_tasks_by_status('в работе', userid=userid)
    performed = task_service.get_tasks_by_status('выполнено', userid=userid)
    for item in performed:
        if item['status'] == 'выполнено':
            item['priority'] += '\U00002705'
    tasks.extend(performed)
    return {'tasks': tasks}


async def archive_getter(dialog_manager: DialogManager, **kwargs):
    userid = dialog_manager.middleware_data['event_from_user'].id
    tasks = task_service.get_tasks_by_status('закрыто', userid=userid)
    return {'tasks': tasks}


main_dialog = Dialog(
    Window(
        Const('Главное меню:'),
        Row(
            Button(Const('Назначенные'), id='worker_assigned', on_click=on_assigned),
            Button(Const('В работе'), id='worker_in_progress', on_click=on_progress),
            Button(Const('Архив'), id='worker_archive', on_click=on_archive)
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
                on_click=on_assigned_task

            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=WorkerSG.main),
        state=WorkerSG.assigned,
        getter=assigned_getter
    ),
    Window(
        Const('Заявки в работе:'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='worker_in_progress_tasks',
                item_id_getter=operator.itemgetter('id'),
                items='tasks'
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=WorkerSG.main),
        state=WorkerSG.in_progress,
        getter=in_progress_getter
    ),
    Window(
        Const('Архив заявок:'),
        Column(
            Select(
                Format('{item[title]}'),
                id='worker_archive_tasks',
                item_id_getter=operator.itemgetter('id'),
                items='tasks'
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=WorkerSG.main),
        state=WorkerSG.archive,
        getter=archive_getter
    )
)
