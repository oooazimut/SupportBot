import operator

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import SwitchTo, Row, Select, Column
from aiogram_dialog.widgets.text import Const, Format

from db import task_service
from states import WorkerSG


async def assigned_getter(dialog_manager: DialogManager, **kwargs):
    userid = dialog_manager.middleware_data['event_from_user'].id
    tasks = task_service.get_tasks_by_status('назначено', userid=userid)
    if not tasks:
        await dialog_manager.switch_to(WorkerSG.main)
    return {'tasks': tasks}


main_dialog = Dialog(
    Window(
        Const('Главное меню:'),
        Row(
            SwitchTo(Const('Назначенные'), id='worker_assigned', state=WorkerSG.assigned),
            SwitchTo(Const('В работе'), id='worker_in_progress', state=WorkerSG.in_progress),
            SwitchTo(Const('Архив'), id='worker_archive', state=WorkerSG.archive)
        ),
        state=WorkerSG.main
    ),
    Window(
        Const('Назначенные заявки'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='assigned_tasks',
                item_id_getter=operator.itemgetter('id'),
                items='tasks'
            )),
        state=WorkerSG.assigned,
        getter=assigned_getter
    )
)
