import operator

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Row, Select, Column, Button, SwitchTo, Cancel
from aiogram_dialog.widgets.text import Const, Format

from handlers import operator_handler
from states import OperatorSG, TaskSG, WorkersSG, OpTaskSG, WorkerSendSG

main_dialog = Dialog(
    Window(
        Const("Главное меню:"),
        Row(
            Button(Const('Заявки'), id='tasks', on_click=operator_handler.go_task),
            Button(Const('Работники'), id='slaves', on_click=operator_handler.go_slaves),
        ),
        state=OperatorSG.main
    ),
)
task_dialog = Dialog(
    Window(
        Const('Заявки:'),
        Row(
            Button(Const('Новые заявки'), id='assign', on_click=operator_handler.go_new_task),
            Button(Const('Заявки в работе'), id='done', on_click=operator_handler.go_work_task),
            Button(Const('Архив'), id='archive', on_click=operator_handler.go_archive)
        ),
        Cancel(Const('Назад')),
        state=OpTaskSG.tas
    ),

    Window(
        Const('Новые заявки:'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='new_tasks',
                item_id_getter=operator.itemgetter('id'),
                items='tasks',
                on_click=operator_handler.on_task
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=OpTaskSG.new_task,
        getter=operator_handler.go_new_task
    ),

    Window(
        Const('Заявки в работе:'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='in_progress_tasks',
                item_id_getter=operator.itemgetter('id'),
                items='tasks',
                on_click=operator_handler.on_task
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OpTaskSG.tas),
        state=OpTaskSG.progress_task,
        getter=operator_handler.progress_task_getter,
    ),

    Window(
        Const('Заявки в архиве'),
        Column(
            Select(
                Format('{item[title]}'),
                id='done_tasks',
                item_id_getter=operator.itemgetter('id'),
                items='tasks',
                on_click=operator_handler.on_task
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OpTaskSG.tas),
        state=OpTaskSG.archive_task,
        getter=operator_handler.archive_getter
    ),
)

worker_dialog = Dialog(
    Window(
        Const('Работники:'),
        Row(
            Button(Const('Операторы'), id='assigned', on_click=operator_handler.go_operator),
            Button(Const('Исполнители'), id='worker_archive', on_click=operator_handler.go_worker)
        ),
        Cancel(Const('Назад')),
        state=WorkersSG.main
    ),

    Window(
        Const('Список операторов:'),
        Column(
            Select(
                Format('{item[username]}'),
                id='operators',
                item_id_getter=operator.itemgetter('id'),
                items='un'
            )
        ),

        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=WorkersSG.opr,
        getter=operator_handler.operator_getter
    ),

    Window(
        Const('Список работников:'),
        Column(
            Select(
                Format('{item[name]} {item[surname]}'),
                id='workers',
                item_id_getter=operator.itemgetter('id'),
                items='un'
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=WorkersSG.slv,
        getter=operator_handler.worker_getter
    ),
)


def is_opened(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'назначено'


def not_in_archive(data, widget, manager: DialogManager):
    return manager.start_data['status'] != 'закрыто'


def is_performed(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'выполнено'


def is_in_progress(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'в работе'


edit_task_dialog = Dialog(
    Window(
        Format('{start_data[created]}'),
        Format('{start_data[name]}'),
        Format('{start_data[title]}'),
        Format('{start_data[description]}'),
        Format('Приоритет: {start_data[priority]}'),
        Format('Статус: {start_data[status]}'),
        Button(Const('Создать'), id='open_task', on_click=operator_handler.create_task),
        Button(Const('Инфо от клиента'), id='client_task', on_click=operator_handler.client_info),
        Button(Const('Редактировать'), id='edit_task', on_click=operator_handler.edit_task, when=is_opened),
        Button(Const('Назначить исполнителя'), id='appoint_task', on_click=operator_handler.appoint_task,
               when=not_in_archive),
        Button(Const('Закрыть'), id='close_task', on_click=operator_handler.close_task, when=is_in_progress),
        Cancel(Const('Назад')),
        state=TaskSG.main
    ),
)

# wizard
worker_send_dialog = Dialog(
    Window(
        Const('Исполнители:'),
        Column(
            Select(
                Format('{item[name]} {item[surname]}'),
                id='workers',
                item_id_getter=operator.itemgetter('id'),
                items='un',
                on_click=operator_handler.set_workers
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=WorkerSendSG.set_worker,
        getter=operator_handler.worker_getter
    ),
)
