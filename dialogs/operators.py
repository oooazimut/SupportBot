import operator

from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Row, Select, Column, Button, SwitchTo, Cancel, Start, Back
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Jinja
from magic_filter import F

from getters.operators import task_getter, addition_getter
from handlers import operators
from handlers.operators import on_addit, on_back_to_preview
from states import OperatorSG, WorkersSG, OpTaskSG, TaskCreating


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
                Format('{item[title]} {item[priority]}'),
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
       {{created}}
       Тема: {{title}}
       Описание: {{description if description}}
       Исполнитель: {{username if username}}
       Приоритет: {{priority if priority}}
       Статус: {{status}}
       '''),
        DynamicMedia('resultmedia', when=F['resultmedia']),
        Button(Const('Доп инфо'), id='addit_info', on_click=on_addit, when=F['media_id']),
        Button(Const('Редактировать'), id='edit_task', on_click=operators.edit_task, when=(F['status'] != 'закрыто')),
        Button(Const('Закрыть'), id='close_task', on_click=operators.on_close, when=(F['status'] != 'закрыто')),
        Cancel(Const('Назад')),
        state=OpTaskSG.preview,
        getter=task_getter
    ),
    Window(
        DynamicMedia('media'),
        Button(Const('Назад'), id='to_preview', on_click=on_back_to_preview),
        state=OpTaskSG.additional,
        getter=addition_getter
    )
)


async def next_or_end(event, widget, dialog_manager: DialogManager, *_):
    if dialog_manager.dialog_data.get('finished'):
        await dialog_manager.switch_to(TaskCreating.preview)
    else:
        await dialog_manager.next()


CANCEL_EDIT = SwitchTo(
    Const("Отменить редактирование"),
    when=F["dialog_data"]['finished'],
    id="cnl_edt",
    state=TaskCreating.preview
)

worker_dialog = Dialog(
    Window(
        Const('Работники:'),
        Row(
            Button(Const('Операторы'), id='assigned', on_click=operators.go_operator),
            Button(Const('Исполнители'), id='worker_archive', on_click=operators.go_worker),
            Button(Const('Добавить работника'), id='add_worker', on_click=operators.go_addslaves),
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
        Const('Введите имя сотрудника'),
        TextInput(id='user_name', on_success=next_or_end),
        Back(Const('Назад')),
        CANCEL_EDIT,
        Cancel(Const('Отменить создание')),
        state=WorkersSG.add_slv
    ),
    Window(
        Const('Введите id сотрудника'),
        TextInput(id='user_id', on_success=next_or_end),
        Back(Const('Назад')),
        Cancel(Const('Отменить создание')),
        state=WorkersSG.add_id
    ),
    Window(
        Const('Выберите статус для сотрудника'),
        Column(
            Button(Const('Исполнитель'), id='slaves_status', on_click=operators.insert_slaves),
            Button(Const('Оператор'), id='operator_status', on_click=operators.insert_operator)
        ),
        Back(Const('Назад')),
        CANCEL_EDIT,
        state=WorkersSG.status

    )
)
