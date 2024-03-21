import datetime

from aiogram import F, Bot
from aiogram.enums import ContentType
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import SwitchTo, Button
from aiogram_dialog.widgets.text import Const
from apscheduler.schedulers.asyncio import AsyncIOScheduler

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
    dialog_manager.dialog_data['priority'] = data

async def on_entity(event, select, dialog_manager: DialogManager, data: str, /):
    dialog_manager.dialog_data['entity'] = data


async def task_description_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    def is_empl(userid):
        user = empl_service.get_employee(userid)
        if user:
            return True

    txt = message.caption
    media_id = None
    match message.content_type:
        case ContentType.TEXT:
            txt = message.text
        case ContentType.PHOTO:
            media_id = message.photo[-1].file_id
        case ContentType.DOCUMENT:
            media_id = message.document.file_id
        case ContentType.VIDEO:
            media_id = message.video.file_id
        case ContentType.AUDIO:
            media_id = message.audio.file_id
        case ContentType.VOICE:
            media_id = message.voice.file_id
        case ContentType.VIDEO_NOTE:
            media_id = message.video_note.file_id
    media_type = message.content_type
    manager.dialog_data['txt'] = txt
    manager.dialog_data['mediaid'] = media_id
    manager.dialog_data['mediatype'] = media_type

    if is_empl(message.from_user.id):
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
    await clb.answer('Ваша заявка принята в обработку и скоро появится в списке ваших заявок.', show_alert=True)

async def reminders_task_to_worker(cls, bot: Bot, scheduler: AsyncIOScheduler, manager: DialogManager):
    tasks=task_service.get_task_reminder(params=None)
    for task in tasks:
        bot = manager.middleware_data['bot']
        await bot.send_message(chat_id=tasks['slave'], text='У вас не выполненная задача с высоким приорететом')
async def reminders_task_to_morning(cls, bot: Bot, scheduler: AsyncIOScheduler):
    tasks=task_service.get_task_reminder_for_morning(params=None)
    for task in tasks:
        await bot.send_message(chat_id=tasks['slave'], text='У вас еще остались не завершенные дела')