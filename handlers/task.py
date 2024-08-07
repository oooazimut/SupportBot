import datetime

from aiogram import F
from aiogram.enums import ContentType
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import SwitchTo, Button
from aiogram_dialog.widgets.text import Const
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import empl_service, task_service
from db.service import EntityService
from jobs import new_task
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


async def on_act(event, select, dialog_manager: DialogManager, data, /):
    dialog_manager.dialog_data['task']['act'] = data


async def on_entity(event, select, dialog_manager: DialogManager, data: str, /):
    entity = EntityService.get_entity(data)[0]
    dialog_manager.dialog_data['task']['entity'] = entity['ent_id']
    dialog_manager.dialog_data['task']['name'] = entity['name']


async def on_slave(event, select, dialog_manager: DialogManager, data: str, /):
    dialog_manager.dialog_data['task']['slave'] = data
    user = empl_service.get_employee(data)
    dialog_manager.dialog_data['task']['username'] = user['username']


async def on_agreementer(event, select, dialog_manager: DialogManager, data: str, /):
    dialog_manager.dialog_data['task']['agreement'] = data


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
    await manager.switch_to(state=TaskCreating.sub_entity, show_mode=ShowMode.DELETE_AND_SEND)


async def to_phone(event, button, manager: DialogManager):
    await manager.switch_to(state=TaskCreating.enter_phone, show_mode=ShowMode.DELETE_AND_SEND)


async def to_title(event, button, manager: DialogManager):
    await manager.switch_to(state=TaskCreating.enter_title, show_mode=ShowMode.DELETE_AND_SEND)


async def to_description(event, button, manager: DialogManager):
    await manager.switch_to(state=TaskCreating.enter_description, show_mode=ShowMode.DELETE_AND_SEND)


async def to_slave(event, button, manager: DialogManager):
    await manager.switch_to(state=TaskCreating.slave, show_mode=ShowMode.DELETE_AND_SEND)


async def to_priority(event, button, manager: DialogManager):
    await manager.switch_to(state=TaskCreating.priority, show_mode=ShowMode.DELETE_AND_SEND)


async def to_act(event, button, manager: DialogManager):
    await manager.switch_to(state=TaskCreating.act, show_mode=ShowMode.DELETE_AND_SEND)


async def to_agreement(event, button, manager: DialogManager):
    await manager.switch_to(state=TaskCreating.agreements, show_mode=ShowMode.DELETE_AND_SEND)


async def cancel_edit(event, button, manager: DialogManager):
    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


async def on_confirm(clb: CallbackQuery, button: Button, manager: DialogManager):
    def is_exist(someone_task: dict):
        return someone_task.get('taskid') is not None

    data: dict = manager.dialog_data.get('task', {})
    data.setdefault('created', datetime.datetime.now().replace(microsecond=0))
    data.setdefault('creator', clb.from_user.id)
    if data.get('slave'):
        data['status'] = 'назначено'
    data.setdefault('status', 'открыто')
    data.setdefault('slave', None)
    data.setdefault('entity', None)
    data.setdefault('agreement', None)
    data.setdefault('priority', None)
    if is_exist(data):
        task_service.update_task(data)
        scheduler: AsyncIOScheduler = manager.middleware_data['scheduler']
        job = scheduler.get_job(job_id='delay' + str(data['taskid']))
        if job:
            job.remove()
        await clb.answer('Заявка отредактирована.', show_alert=True)
    else:
        task = task_service.save_task(data)
        await clb.answer('Заявка принята в обработку и скоро появится в списке заявок объекта.', show_alert=True)
        users = empl_service.get_employees_by_position('operator')
        userids = [user['userid'] for user in users]
        slaveid = data.get('slave')
        if slaveid:
            userids.append(slaveid)

        scheduler: AsyncIOScheduler = manager.middleware_data['scheduler']
        for userid in userids:
            scheduler.add_job(new_task, 'cron', minute='*/5', hour='9-17',
                              args=[userid, task['title'], task['taskid']], id=str(userid) + str(task['taskid']),
                              replace_existing=True)

    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


async def on_start(data, manager: DialogManager):
    if manager.start_data:
        manager.dialog_data['task'] = manager.start_data
    else:
        manager.dialog_data['task'] = dict()


async def on_return(clb: CallbackQuery, button, manager: DialogManager):
    taskid = manager.start_data['taskid']
    task = task_service.get_task(taskid)[0]
    if task['slave']:
        task_service.change_status(taskid, 'в работе')
    else:
        task_service.change_status(taskid, 'открыто')
    scheduler: AsyncIOScheduler = manager.middleware_data['scheduler']
    job = scheduler.get_job(str(manager.start_data['taskid']))
    if job:
        job.remove()
        await clb.answer('Заявка возвращена в работу.', show_alert=True)
    else:
        await clb.answer('Заявка уже в работе.', show_alert=True)
    await manager.done()


async def on_del_performer(clb: CallbackQuery, button, manager: DialogManager):
    manager.dialog_data['task']['slave'] = None
    manager.dialog_data['task']['username'] = None
    await clb.answer('Исполнитель убран из заявки.', show_alert=True)
