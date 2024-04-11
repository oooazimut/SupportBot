import asyncio
import datetime
import operator

from aiogram import Bot
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Row, Select, Column, Button, SwitchTo, Cancel, Back
from aiogram_dialog.widgets.text import Const, Format
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import task_service
from getters.workers import task_entities_getter, tasks_open_getter
from handlers.workers import on_assigned, on_archive, on_progress, on_task, entites_name_handler, \
    open_tasks, on_entity
from jobs import close_task
from states import WorkerSG, WorkerTaskSG, PerformedTaskSG


async def task_getter(dialog_manager: DialogManager, **kwargs):
    userid = str(dialog_manager.middleware_data['event_from_user'].id)
    tasks = dialog_manager.dialog_data[userid]
    return {'tasks': tasks}


main_dialog = Dialog(
    Window(
        Const('Главное меню:'),
        Row(
            Button(Const('Назначенные'), id='worker_assigned', on_click=on_assigned),
            Button(Const('В работе'), id='worker_in_progress', on_click=on_progress),
            Button(Const('Архив'), id='worker_archive', on_click=on_archive),
            SwitchTo(Const('Заявки по объектам'), id='tasks_for_entity', state=WorkerSG.entities_search)
        ),
        state=WorkerSG.main
    ),
    Window(
        Const('Назначенные заявки'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='worker_assigned_tasks',
                item_id_getter=operator.itemgetter('taskid'),
                items='tasks',
                on_click=on_task

            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=WorkerSG.main),
        state=WorkerSG.assigned,
        getter=task_getter
    ),
    Window(
        Const('Заявки в работе:'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='worker_in_progress_tasks',
                item_id_getter=operator.itemgetter('taskid'),
                items='tasks',
                on_click=on_task
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=WorkerSG.main),
        state=WorkerSG.in_progress,
        getter=task_getter
    ),
    Window(
        Const('Архив заявок:'),
        Column(
            Select(
                Format('{item[title]}'),
                id='worker_archive_tasks',
                item_id_getter=operator.itemgetter('taskid'),
                items='tasks',
                on_click=on_task
            )
        ),
        SwitchTo(Const('Назад'), id='to_main', state=WorkerSG.main),
        state=WorkerSG.archive,
        getter=task_getter
    ),
    Window(
        Const('Выбор объекта. Для получение объекта/объектов введите его название или хотя бы часть.'),
        MessageInput(entites_name_handler, content_types=[ContentType.TEXT]),
        state=WorkerSG.entities_search
    ),
    Window(
        Const('Объекты'),
        Select(
            Format('{item[name]}'),
            id='objects',
            item_id_getter=operator.itemgetter('ent_id'),
            items='objects',
            on_click=on_entity
        ),
        state=WorkerSG.enter_object,
        getter=task_entities_getter
    ),
    Window(
        Const('Заявки на обьекте:'),
        Column(
            Select(
            Format('{item[title]} {item[priority]}'),
            id='tasks',
            item_id_getter=operator.itemgetter('taskid'),
            items='tasks',
            on_click=open_tasks
            ),
            Back(Const('Назад')),
        ),

        state=WorkerSG.tasks_entities,
        getter=tasks_open_getter

    ),
)


async def accept_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    task_service.change_status(manager.start_data['taskid'], 'в работе')
    await callback.answer(f'Заявка {manager.start_data["title"]} принята в работу.')


async def refuse_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    task_service.change_status(manager.start_data['taskid'], 'открыто')
    await callback.answer(f'Вы отказались от заявки:  {manager.start_data["title"]}')


async def onclose_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(WorkerTaskSG.media_pin)


async def get_back(callback: CallbackQuery, button: Button, manager: DialogManager):
    task_service.change_status(manager.start_data['taskid'], 'в работе')
    await callback.answer(f'Заявка {manager.start_data["title"]} снова в работе.')


async def client_info(callback: CallbackQuery, button: Button, manager: DialogManager):
    pass


def is_opened(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'назначено'


def not_in_archive(data, widget, manager: DialogManager):
    return manager.start_data['status'] != 'закрыто'


def is_performed(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'выполнено'


def is_in_progress(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'в работе'


async def media_pin_task(message: Message, message_input: MessageInput, manager: DialogManager, callback=CallbackQuery):
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

    task_service.save_result(txt, media_id, media_type, manager.start_data['taskid'])
    task_service.change_status(manager.start_data['taskid'], 'выполнено')
    mes = await message.answer(f'Заявка {manager.start_data["title"]} выполнена. Ожидаем потверждения от клиента.')

    taskid = manager.start_data['taskid']
    user = manager.start_data['creator']
    run_date = datetime.datetime.now() + datetime.timedelta(days=3)
    scheduler: AsyncIOScheduler = manager.middleware_data['scheduler']
    bg = manager.bg(user_id=user, chat_id=user)

    task_service.change_status(taskid, 'выполнено')
    scheduler.add_job(close_task, trigger='date', run_date=run_date, args=[taskid], id=str(taskid))
    await bg.start(state=PerformedTaskSG.main, data={'taskid': taskid})

    await asyncio.sleep(5)
    await mes.delete()
    await manager.done()
    
task_dialog = Dialog(
    Window(
        Format('{start_data[created]}'),
        Format('{start_data[name]}'),
        Format('{start_data[title]}'),
        Format('{start_data[description]}'),
        Format('Приоритет: {start_data[priority]}'),
        Format('Статус: {start_data[status]}'),
        Button(Const('Принять'), id='accept_task', on_click=accept_task, when=is_opened),
        Button(Const('Отказаться'), id='refuse_task', on_click=refuse_task, when=not_in_archive),
        Button(Const('Закрыть'), id='close_task', on_click=onclose_task, when=not_in_archive),
        Button(Const('Вернуть в работу'), id='back_to_work', on_click=get_back, when=is_performed),
        Cancel(Const('Назад')),
        state=WorkerTaskSG.main
    ),
    Window(
       Const('Требуется отчет о проделанной работе. Это может быть картинка, видео, текст или голосовое сообщение.'),
        MessageInput(media_pin_task, content_types=[ContentType.ANY]),
        SwitchTo(Const('Назад'), id='to_main', state=WorkerSG.main),
        state=WorkerTaskSG.media_pin
    )
)