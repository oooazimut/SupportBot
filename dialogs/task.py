import operator

from aiogram import F
from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import SwitchTo, Cancel, Back, Radio, Button
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Jinja, Format

from getters.task import priority_getter, result_getter
from handlers.task import next_or_end, CANCEL_EDIT, task_description_handler, on_priority, ent_name_handler, on_confirm
from states import TaskCreating

create_task_dialog = Dialog(
    Window(
        Const('Введите название организации или объекта'),
        TextInput(id='entity_input', on_success=next_or_end),
        CANCEL_EDIT,
        Cancel(Const('Отменить создание')),
        state=TaskCreating.enter_entity
    ),
    Window(
        Const('Ваш номер телефона:'),
        TextInput(id='phone_input', on_success=next_or_end),
        Back(Const('Назад')),
        CANCEL_EDIT,
        Cancel(Const('Отменить создание')),
        state=TaskCreating.enter_phone
    ),
    Window(
        Const('Тема обращения?'),
        TextInput(id='title_input', on_success=next_or_end),
        CANCEL_EDIT,
        Back(Const('Назад')),
        Cancel(Const('Отменить создание')),
        state=TaskCreating.enter_title
    ),
    Window(
        Const('Опишите вашу проблему. Это может быть текстовое, голосовое, видеосообщение или картинка.'),
        MessageInput(task_description_handler, content_types=[ContentType.ANY]),
        Back(Const('Назад')),
        CANCEL_EDIT,
        Cancel(Const('Отменить создание')),
        state=TaskCreating.enter_description
    ),
    Window(
        Const('Выбор приоритета:'),
        Radio(
            Format('🔘 {item[0]}'),
            Format('⚪️ {item[0]}'),
            id='ch_prior',
            item_id_getter=operator.itemgetter(1),
            items='priorities',
            on_click=on_priority
        ),
        Button(Const('Подтвердить'), id='confirm_priority', on_click=next_or_end),
        getter=priority_getter,
        state=TaskCreating.priority
    ),
    Window(
        Const('Выбор объекта. Для получение объекта/объектов введите его название или хотя бы часть.'),
        MessageInput(ent_name_handler, content_types=[ContentType.TEXT]),
        state=TaskCreating.entity
    ),
    Window(
        Const('Назначить работника'),
        # Radio(),
        state=TaskCreating.slave
    ),
    Window(
        Jinja('''
        Ваша заявка:

        <b>Объект</b>: {{entity}}
        <b>Телефон</b>: {{phone}}
        <b>Тема</b>: {{title}}
        <b>Описание</b>: {{description if description}}
        '''),
        DynamicMedia('media', when=F['dialog_data']['mediaid']),
        Cancel(Const('Сохранить'), id='confirm_creating', on_click=on_confirm),
        SwitchTo(Const('Изменить объект'), state=TaskCreating.enter_entity, id='to_entity'),
        SwitchTo(Const('Изменить телефон'), state=TaskCreating.enter_phone, id='to_phone'),
        SwitchTo(Const('Изменить Тему'), state=TaskCreating.enter_title, id='to_title'),
        SwitchTo(Const('Изменить описание'), state=TaskCreating.enter_description, id='to_description'),
        Cancel(Const('Отменить создание')),
        state=TaskCreating.preview,
        getter=result_getter,
        parse_mode='html'
    )
)
