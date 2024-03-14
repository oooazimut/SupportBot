import datetime
from typing import Any

from aiogram.enums import ContentType
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button

from db import task_service
from states import CustomerSG, CustomerTaskSG, TaskCreating


async def task_description_handler(message: Message, message_input: MessageInput, manager: DialogManager):
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

    await manager.switch_to(TaskCreating.preview)


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


async def tasks_handler(callback: CallbackQuery, button: Button, manager: DialogManager):
    userid = str(callback.from_user.id)
    tasks = task_service.get_active_tasks(userid)
    if tasks:
        manager.dialog_data[userid] = tasks
        await manager.switch_to(CustomerSG.active_tasks)
    else:
        await callback.answer('Нет активных заявок.')


async def archive_handler(callback: CallbackQuery, button: Button, manager: DialogManager):
    userid = str(callback.from_user.id)
    bot = manager.middleware_data['bot']

    tasks = task_service.get_archive_tasks(userid)
    if tasks:
        await callback.message.answer(f'Объект: {tasks[0]["name"]}\n Закрытые заявки: ')
        for task in tasks:
            await bot.send_message(chat_id=userid, text=task['created'] + '\n' + task['title'])
            for mess_id in task['client_info'].split():
                await bot.forward_message(chat_id=userid, from_chat_id=userid, message_id=mess_id)
    else:
        await callback.answer('Архив пустой.')


async def on_task(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    userid = str(callback.from_user.id)
    task = next((t for t in manager.dialog_data[userid] if t['id'] == int(item_id)), None)
    await manager.start(CustomerTaskSG.main, data=task)
