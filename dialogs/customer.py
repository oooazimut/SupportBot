from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import Start, Next, Cancel, Back, Button
from aiogram_dialog.widgets.text import Const

from handlers import customer_handlers
from states import TaskCreating, CustomerSG

main_dialog = Dialog(
    Window(
        Const('Вас приветствует бот технической поддержки компании "Азимут"'),
        Start(Const('Создать заявку'), id='start_creating', state=TaskCreating.enter_entity),
        Button(Const('Активные заявки'), id='customer_tasks', on_click=customer_handlers.tasks_handler),
        Button(Const('Архив'), id='customer_archive', on_click=customer_handlers.archive_handler),
        state=CustomerSG.main
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
