from aiogram import F
from aiogram.enums import ContentType
from aiogram.types import Message
from aiogram_dialog import DialogManager, Dialog, Window
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import SwitchTo, Cancel, Back, ScrollingGroup, Radio
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Jinja

from db import empl_service
from handlers.customer_handlers import task_description_handler, on_confirm
from states import TaskCreating

CANCEL_EDIT = SwitchTo(
    Const("Отменить редактирование"),
    when=F["dialog_data"]['finished'],
    id="cnl_edt",
    state=TaskCreating.preview
)


async def next_or_end(event, widget, dialog_manager: DialogManager, *_):
    print(type(event), _)
    if dialog_manager.dialog_data.get('finished'):
        await dialog_manager.switch_to(TaskCreating.preview)
    else:
        await dialog_manager.next()


async def op_next_end(event: Message, widget, dialog_manager: DialogManager, *_):
    def is_empl(userid):
        user = empl_service.get_employee(userid)
        if user:
            return True

    if dialog_manager.dialog_data.get('finished'):
        await dialog_manager.switch_to(TaskCreating.preview)
    else:
        if is_empl(event.from_user.id):
            await dialog_manager.next()
        else:
            pass



async def result_getter(dialog_manager: DialogManager, **kwargs):
    if dialog_manager.start_data:
        dialog_manager.dialog_data['task'] = dialog_manager.start_data
    mediatype = dialog_manager.dialog_data['mediatype']
    mediaid = dialog_manager.dialog_data['mediaid']
    media = MediaAttachment(mediatype, file_id=MediaId(mediaid))
    dialog_manager.dialog_data['finished'] = True

    return {
        "entity": dialog_manager.find('entity_input').get_value(),
        "phone": dialog_manager.find('phone_input').get_value(),
        "title": dialog_manager.find('title_input').get_value(),
        "description": dialog_manager.dialog_data['txt'],
        'media': media
    }


create_task_dialog = Dialog(
    Window(
        Const('Введите название организации или объекта'),
        TextInput(id='entity_input', on_success=next_or_end),
        CANCEL_EDIT,
        Cancel(Const('Отменить создание')),
        state=TaskCreating.enter_entity
    ),
    Window(
        Const('Введите номер телефона, по которому с вами можно будет связаться'),
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
        state=TaskCreating.priority
    ),
    Window(
        Const('Выбор объекта:'),
        ScrollingGroup(),
        state= TaskCreating.entity
    ),
    Window(
        Const('Назначить работника'),
        Radio(),
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
