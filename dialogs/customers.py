import operator

from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import Start, Next, Cancel, Back, Button, Select, Column
from aiogram_dialog.widgets.text import Const, Format, Jinja

from handlers import customer_handlers
from handlers.customer_handlers import on_task
from states import TaskCreating, CustomerSG, CustomerTaskSG


async def tasks_getter(dialog_manager: DialogManager, **kwargs):
    userid = str(dialog_manager.middleware_data['event_from_user'].id)
    tasks = dialog_manager.dialog_data[userid]
    return {'tasks': tasks}


main_dialog = Dialog(
    Window(
        Const('Вас приветствует бот технической поддержки компании "Азимут"'),
        Start(Const('Создать заявку'), id='start_creating', state=TaskCreating.enter_entity),
        Button(Const('Активные заявки'), id='customer_tasks', on_click=customer_handlers.tasks_handler),
        Button(Const('Архив'), id='customer_archive', on_click=customer_handlers.archive_handler),
        state=CustomerSG.main
    ),
    Window(
        Format('{tasks[0][name]}'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='customer_active_tasks',
                item_id_getter=operator.itemgetter('id'),
                items='tasks',
                on_click=on_task
            )
        ),
        state=CustomerSG.active_tasks,
        getter=tasks_getter
    ),

)

create_task_dialog = Dialog(
    Window(
        Const('Введите название организации или объекта'),
        TextInput(id='entity_input', on_success=Next()),
        Cancel(Const('Отмена')),
        state=TaskCreating.enter_entity
    ),
    Window(
        Const('Введите номер телефона, по которому с вами можно будет связаться'),
        TextInput(id='phone_input', on_success=Next()),
        Back(Const('Назад')),
        Cancel(Const('Отмена')),
        state=TaskCreating.enter_phone
    ),
    Window(
        Const('Тема обращения?'),
        TextInput(id='title_input', on_success=Next()),
        Back(Const('Назад')),
        Cancel(Const('Отмена')),
        state=TaskCreating.enter_title
    ),
    Window(
        Const('Опишите вашу проблему. Это может быть текстовое, голосовое, видеосообщение или картинка.'),
        MessageInput(customer_handlers.task_description_handler, content_types=[ContentType.ANY]),
        Back(Const('Назад')),
        Cancel(Const('Отмена')),
        state=TaskCreating.enter_description
    )
)


async def task_getter(dialog_manager: DialogManager, **kwargs):
    return dialog_manager.start_data


task_dialog = Dialog(
    Window(
        Jinja("""
       {{created}}
       <b>{{title}}</b>
       {{description}}
       {{client_info}}
       """),
        Cancel(Const('Назад')),
        parse_mode='HTML',
        state=CustomerTaskSG.main,
        getter=task_getter

    )
)
