import operator

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.kbd import Row, Select, Column, Button, SwitchTo, Cancel, Start
from aiogram_dialog.widgets.text import Const, Format, Jinja

from handlers import operators
from states import OperatorSG, WorkersSG, OpTaskSG, TaskCreating


def is_opened(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'назначено'


def not_in_archive(data, widget, manager: DialogManager):
    return manager.start_data['status'] != 'закрыто'


def is_performed(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'выполнено'


main_dialog = Dialog(
    Window(
        Const("Главное меню:"),
        Row(
            Button(Const('Заявки'), id='tasks', on_click=operators.go_task),
            Button(Const('Работники'), id='slaves', on_click=operators.go_slaves),
        ),
        state=OperatorSG.main
    ),
)
task_dialog = Dialog(
    Window(
        Const('Заявки:'),
        Row(
            Button(Const('Новые заявки'), id='assign', on_click=operators.go_new_task),
            Button(Const('Заявки в работе'), id='done', on_click=operators.go_work_task),
            Button(Const('Архив'), id='archive', on_click=operators.go_archive)
        ),
        Start(Const('Создать заявку'), id='new_op_task', data={}, state=TaskCreating.sub_entity),
        Cancel(Const('Назад')),
        state=OpTaskSG.tas
    ),

    Window(
        Const('Новые заявки:'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='new_tasks',
                item_id_getter=operator.itemgetter('taskid'),
                items='tasks',
                on_click=operators.on_task
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OpTaskSG.tas),
        state=OpTaskSG.new_task,
        getter=operators.tasks_getter
    ),

    Window(
        Const('Заявки в работе:'),
        Column(
            Select(
                Format('{item[title]} {item[priority]} {item[emoji]}'),
                id='in_progress_tasks',
                item_id_getter=operator.itemgetter('taskid'),
                items='tasks',
                on_click=operators.on_task
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OpTaskSG.tas),
        state=OpTaskSG.progress_task,
        getter=operators.tasks_getter,
    ),

    Window(
        Const('Заявки в архиве'),
        Column(
            Select(
                Format('{item[title]}'),
                id='done_tasks',
                item_id_getter=operator.itemgetter('taskid'),
                items='tasks',
                on_click=operators.on_task
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OpTaskSG.tas),
        state=OpTaskSG.archive_task,
        getter=operators.tasks_getter
    ),
    Window(
        Jinja('''
       {{start_data.created}}
       Тема: {{start_data.title}}
       Описание: {{start_data.description if start_data.description}}
       Исполнитель: {{start_data.username if start_data.username}}
       Приоритет: {{start_data.priority if start_data.priority}}
       Статус: {{start_data.status}}
       '''),
        Button(Const('Редактировать'), id='edit_task', on_click=operators.edit_task, when=not_in_archive),
        Button(Const('Закрыть'), id='close_task', on_click=operators.on_close, when=not_in_archive),
        Cancel(Const('Назад')),
        state=OpTaskSG.preview
    )
)

worker_dialog = Dialog(
    Window(
        Const('Работники:'),
        Row(
            Button(Const('Операторы'), id='assigned', on_click=operators.go_operator),
            Button(Const('Исполнители'), id='worker_archive', on_click=operators.go_worker)
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
                item_id_getter=operator.itemgetter('userid'),
                items='un'
            )
        ),

        SwitchTo(Const('Назад'), id='to_main', state=WorkersSG.main),
        state=WorkersSG.opr,
        getter=operators.operator_getter
    ),

    Window(
        Const('Список работников:'),
        Column(
            Select(
                Format('{item[username]}'),
                id='workers',
                item_id_getter=operator.itemgetter('userid'),
                items='un'
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=WorkersSG.main),
        state=WorkersSG.slv,
        getter=operators.worker_getter
    ),
    Window(

    )
)
