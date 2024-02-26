import datetime
import operator

from aiogram import F
from aiogram.enums import ContentType
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.kbd import Start, Cancel, Back, Button, Select, Column, SwitchTo
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Jinja

from db import task_service
from handlers import customer_handlers
from handlers.customer_handlers import on_task
from states import TaskCreating, CustomerSG, CustomerTaskSG


async def tasks_getter(dialog_manager: DialogManager, **kwargs):
    userid = str(dialog_manager.middleware_data['event_from_user'].id)
    tasks = dialog_manager.dialog_data[userid]
    return {'tasks': tasks}


async def shit_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    await message.delete()


main_dialog = Dialog(
    Window(
        Const('Вас приветствует бот технической поддержки компании "Азимут"'),
        Start(Const('Создать заявку'), id='start_creating', state=TaskCreating.enter_entity),
        Button(Const('Активные заявки'), id='customer_tasks', on_click=customer_handlers.tasks_handler),
        Button(Const('Архив'), id='customer_archive', on_click=customer_handlers.archive_handler),
        MessageInput(func=shit_handler),
        state=CustomerSG.main,
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
        Back(Const('Назад')),
        state=CustomerSG.active_tasks,
        getter=tasks_getter
    )

)


CANCEL_EDIT = SwitchTo(
    Const("Отменить редактирование"),
    when=F["dialog_data"]['finished'],
    id="cnl_edt",
    state=TaskCreating.preview
)


async def next_or_end(event, widget, dialog_manager: DialogManager, *_):
    if dialog_manager.dialog_data.get('finished'):
        await dialog_manager.switch_to(TaskCreating.preview)
    else:
        await dialog_manager.next()


async def result_getter(dialog_manager: DialogManager, **kwargs):
    dialog_manager.dialog_data['finished'] = True
    mediatype = dialog_manager.dialog_data['mediatype']
    mediaid = dialog_manager.dialog_data['mediaid']
    media = MediaAttachment(mediatype, file_id=MediaId(mediaid))

    return {
        "entity": dialog_manager.find('entity_input').get_value(),
        "phone": dialog_manager.find('phone_input').get_value(),
        "title": dialog_manager.find('title_input').get_value(),
        "description": dialog_manager.dialog_data['txt'],
        'media': media
    }

async def on_confirm(clb: CallbackQuery, button: Button, manager: DialogManager):
    mediatype = manager.dialog_data['mediatype']
    mediaid = manager.dialog_data['mediaid']
    curr_time = datetime.datetime.now().replace(microsecond=0)
    creator = clb.from_user.id
    phone = manager.find('phone_input').get_value()
    title = manager.find('entity_input').get_value() + ': ' + manager.find('title_input').get_value()
    client_info = manager.dialog_data['txt']
    status = 'открыто'
    priority = ''
    params = [
        curr_time,
        creator,
        phone,
        title,
        client_info,
        mediatype,
        mediaid,
        status,
        priority
    ]
    task_service.save_task(params=params)
    await clb.answer('Ваша заявка принята в обработку и скоро появится в списке ваших заявок.')


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
        MessageInput(customer_handlers.task_description_handler, content_types=[ContentType.ANY]),
        Back(Const('Назад')),
        CANCEL_EDIT,
        Cancel(Const('Отменить создание')),
        state=TaskCreating.enter_description
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


async def media_getter(dialog_manager: DialogManager, **kwargs):
    mediaid = dialog_manager.start_data['media_id']
    mediatype = dialog_manager.start_data.get('media_type')
    media = MediaAttachment(mediatype, file_id=MediaId(mediaid))
    return {'media': media}


task_dialog = Dialog(
    Window(
        Jinja("""
       {{start_data.created}}
       <b>{{start_data.title}}</b>
       {{start_data.description if start_data.description}}
       {{start_data.client_info if start_data.client_info}}
       """),
        DynamicMedia('media', when=F['start_data']['media_id']),
        Cancel(Const('Назад')),
        parse_mode='HTML',
        state=CustomerTaskSG.main,
        getter=media_getter

    )
)
