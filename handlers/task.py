import datetime

from aiogram import F
from aiogram.enums import ContentType
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import SwitchTo, Button
from aiogram_dialog.widgets.text import Const

from db import empl_service, task_service
from db.service import EntityService
from states import TaskCreating

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


async def on_priority(event, select, dialog_manager: DialogManager, data: str, /):
    dialog_manager.dialog_data['task']['priority'] = data


async def on_entity(event, select, dialog_manager: DialogManager, data: str, /):
    data = eval(data)
    dialog_manager.dialog_data['task']['entity'] = data['ent_id']
    dialog_manager.dialog_data['task']['name'] = data['name']


async def on_slave(event, select, dialog_manager: DialogManager, data: str, /):
    dialog_manager.dialog_data['task']['slave'] = data
    user = empl_service.get_employee(data)
    dialog_manager.dialog_data['task']['username'] = user['username']


async def task_description_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    def is_empl(userid):
        user = empl_service.get_employee(userid)
        if user:
            return True
    txt = ''
    media_id = None
    match message.content_type:
        case ContentType.TEXT:
            txt = message.text
        case ContentType.PHOTO:
            media_id = message.photo[-1].file_id
            txt = message.caption
        case ContentType.DOCUMENT:
            media_id = message.document.file_id
            txt = message.caption
        case ContentType.VIDEO:
            media_id = message.video.file_id
            txt = message.caption
        case ContentType.AUDIO:
            media_id = message.audio.file_id
            txt = message.caption
        case ContentType.VOICE:
            media_id = message.voice.file_id
        case ContentType.VIDEO_NOTE:
            media_id = message.video_note.file_id
    media_type = message.content_type
    manager.dialog_data['task']['description'] = txt
    manager.dialog_data['task']['media_id'] = media_id
    manager.dialog_data['task']['media_type'] = media_type

    if is_empl(message.from_user.id) and not manager.dialog_data.get('finished'):
        await manager.next()
    else:
        await manager.switch_to(TaskCreating.preview)


async def ent_name_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    entities = EntityService.get_entities_by_substr(message.text)
    if entities:
        manager.dialog_data['entities'] = entities
        await manager.switch_to(TaskCreating.entities)
    else:
        await manager.switch_to(TaskCreating.empty_entities)

async def to_entity(event, button, manager: DialogManager):
    await manager.switch_to(state=TaskCreating.sub_entity, show_mode=ShowMode.SEND)

async def to_phone(event, button, manager: DialogManager):
    await manager.switch_to(state=TaskCreating.enter_phone, show_mode=ShowMode.SEND)

async def to_title(event, button, manager: DialogManager):
    await manager.switch_to(state=TaskCreating.enter_title, show_mode=ShowMode.SEND)

async def to_description(event, button, manager: DialogManager):
    await manager.switch_to(state=TaskCreating.enter_description, show_mode=ShowMode.SEND)

async def cancel_edit(event, button, manager: DialogManager):
    await manager.done(show_mode=ShowMode.SEND)

async def on_confirm(clb: CallbackQuery, button: Button, manager: DialogManager):
    created = manager.start_data.get('created') or datetime.datetime.now().replace(microsecond=0)
    creator = manager.start_data.get('creator') or clb.from_user.id
    phone = manager.dialog_data['to_save']['phone']
    title = manager.dialog_data['to_save']['title']
    description = manager.dialog_data['to_save']['description']
    media_type = manager.dialog_data['task'].get('media_type') or manager.start_data.get('media_type')
    media_id = manager.dialog_data['task'].get('media_id') or manager.start_data.get('media_id')
    status = manager.start_data.get('status') or 'открыто'
    priority = manager.dialog_data['to_save']['priority']
    entity = manager.dialog_data['task'].get('entity') or manager.start_data.get('entity')
    slave = manager.dialog_data['task'].get('slave') or manager.start_data.get('slave')
    if manager.start_data:
        task_service.update_task(phone, title, description, media_type, media_id, status, priority,
                                 entity, slave, manager.start_data['taskid'])
        await clb.answer('Заявка отредактирована.', show_alert=True)
    else:
        task_service.save_task(created, creator, phone, title, description, media_type, media_id, status, priority,
                               entity, slave)
        await clb.answer('Заявка принята в обработку и скоро появится в списке заявок объекта.', show_alert=True)
    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


async def on_start(data, manager: DialogManager):
    manager.dialog_data['task'] = {}
