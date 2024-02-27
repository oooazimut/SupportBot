import operator

from aiogram import F
from aiogram.types import Message
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Row, Select, Column, Button, SwitchTo, Start, Cancel, Toggle, ManagedToggle
from aiogram_dialog.widgets.text import Const, Format, Jinja

from handlers.operator_handler import on_confirm, go_task, go_slaves, go_archive, go_inw_task, go_new_task, \
    worker_getter, operator_getter
from states import OperatorSG, AddWorkerSG
from db import task_service, empl_service





main_dialog = Dialog(
    Window (
        Const("Главное меню:"),
        Row(
            Button(Const('Заявки'), id='tasks', on_click=go_task),
            Button(Const('Работники'), id='slaves', on_click=go_slaves),
        ),
        state = OperatorSG.main
    ),
)
task_dialog = Dialog(
    Window(
        Const('Заявки:'),
           Row(
               Button(Const('Новые заявки'), id='assign', on_click=go_new_task),
               Button(Const('Заявки в работе'), id='done', on_click=go_inw_task),
               Button(Const('Архив'), id='archive', on_click=go_archive)
           ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=OperatorSG.tas
    ),

    Window(
        Const('Новые заявки:'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='new_tasks',
                item_id_getter=operator.itemgetter('id'),
                items=''
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=OperatorSG.new_task,
        getter=task_service.get_tasks
    ),

    Window(
        Const('Заявки в работе:'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='in_progress_tasks',
                item_id_getter=operator.itemgetter('id'),
                items=''
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=OperatorSG.progress_task,
        getter=task_service.get_tasks
    ),

    Window(
        Const('Заявки в архиве'),
      Column(
          Select(
              Format('{item[title]} {item[priority]}'),
              id='done_tasks',
              item_id_getter=operator.itemgetter('id'),
              items=''
          )
      ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state=OperatorSG.archive_task,
        getter=task_service.get_tasks
    ),
)

worker_dialog = Dialog(
    Window(
        Const('Работники:'),
        Row(
            Button(Const('Операторы'), id='assigned', on_click=operator_getter),
            Button(Const('Исполнители'), id='worker_archive', on_click=worker_getter)
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state = OperatorSG.worker
    ),

    Window(
        Const('Список операторов:'),
        Column(
            Select(
                Format('{item[name]} {item[surname]}'),
                id='operators',
                item_id_getter=operator.itemgetter('id'),
                items='un'
            )
        ),

        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        state = OperatorSG.opr,
        getter = operator_getter
    ),

    Window(
      Const('Список работников:'),
        Column(
          Select(
              Format('{item[name]} {item[surname]}'),
              id = 'workers',
              item_id_getter = operator.itemgetter('id'),
              items = 'un'
          )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=OperatorSG.main),
        Start(Const('Добавить работника'), id='to_add_slave', state=AddWorkerSG.name),
        state = OperatorSG.slv,
        getter = worker_getter
    ),
)


async def next_or_end(event, widget, dialog_manager: DialogManager, *_):
    if dialog_manager.dialog_data.get('finished'):
        await dialog_manager.switch_to(AddWorkerSG.preview)
    else:
        await dialog_manager.next()

CANCEL_EDIT = SwitchTo(
    Const("Отменить редактирование"),
    when=F["dialog_data"]['finished'],
    id="cnl_edt",
    state=AddWorkerSG.preview
)

async def user_preview_getter(dialog_manager: DialogManager, **kwargs):
    dialog_manager.dialog_data['finished'] = True
    return {
        'name': dialog_manager.find('worker_name_input').get_value(),
        'userid': dialog_manager.find('worker_id_input').get_value()
    }

async def statustypes_getter(**kwargs):
    return {
        'status_types': [
            (1, 'Оператор'),
            (2, 'Исполнитель')
        ]
    }

def id_getter(status: tuple) -> int:
    return status[0]

async def on_toggle_click(msg: Message, widget: ManagedToggle, manager: DialogManager, data):
    print(data)

add_worker_dialog = Dialog(
    Window(
        Const('Введите имя новоприбывшего:'),
        TextInput(id='worker_name_input', on_success=next_or_end),
        CANCEL_EDIT,
        Cancel(Const('Отменить добавление')),
        state=AddWorkerSG.name
    ),
    Window(
        Const('Введите его ID:'),
        TextInput(id='worker_id_input', on_success=next_or_end),
        CANCEL_EDIT,
        Cancel(Const('Отменить добавление')),
        state=AddWorkerSG.workerid
    ),
    Window(
        Const('Выберите тип выполняемой работы:'),
        Toggle(
            text=Format('{}'),
            id='toggle_status',
            items='status_types',
            item_id_getter=id_getter,
            on_click=on_toggle_click
        ),
        state=AddWorkerSG.status,
        getter=statustypes_getter,
        preview_data=statustypes_getter
    ),
    Window(
        Jinja('''
        Проверьте, все ли правильно:
        <b>Имя</b>: {{name}}
        <b>ID</b>: {{userid}}
        '''),
        Cancel(
            Const('Подтвердить добавление'),
            id='confirm_worker_adding',
            on_click=on_confirm
        ),
        state=AddWorkerSG.preview
    )
)