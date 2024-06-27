import asyncio
import datetime
import operator

from aiogram import F
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, Window, DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Select, Column, Button, SwitchTo, Back
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Jinja
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
from db import task_service, empl_service
from getters.workers import task_entities_getter, tasks_open_getter, media_getter
from handlers.workers import on_assigned, on_archive, on_progress, on_task, entites_name_handler, \
    open_tasks, on_entity, back_to_main, to_entities, on_cancel, act_handler
from jobs import close_task, confirmed_task, agreement_alarm
from states import WorkerSG, WorkerTaskSG

JINJA_TEMPLATE = Jinja('{% set dttm_list = item.created.split() %}'
                       '{% set dt_list = dttm_list[0].split("-") %}'
                       '{% set dt = dt_list[2]+"."+dt_list[1] %}'
                       '{% set em = "\U00002705" if item.status == "выполнено" else "\U0001F7E9" if item.status == "в '
                       'работе" else "" %}'
                       '{% set sl = item.username if item.username else "\U00002753" %}'
                       '{% set pr = item.priority if item.priority else "" %}'
                       '{% set ob = item.name if item.name else "" %}'
                       '{% set tt = item.title if item.title else "" %}'
                       '{% set ag = "\U00002757\U0001F4DE\U00002757" if item.agreement else "" %}'
                       '{{ag}}{{em}} {{dt}} {{pr}} {{sl}} {{ob}} {{tt}}')

TO_MAIN = Button(Const('Назад'), id='back_to_main', on_click=back_to_main)


async def task_getter(dialog_manager: DialogManager, **kwargs):
    userid = str(dialog_manager.middleware_data['event_from_user'].id)
    tasks = dialog_manager.dialog_data[userid]
    return {'tasks': tasks}


main_dialog = Dialog(
    Window(
        Const('Главное меню:'),
        Column(
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
                JINJA_TEMPLATE,
                id='worker_assigned_tasks',
                item_id_getter=operator.itemgetter('taskid'),
                items='tasks',
                on_click=on_task

            )
        ),
        TO_MAIN,
        state=WorkerSG.assigned,
        getter=task_getter
    ),
    Window(
        Const('Заявки в работе:'),
        Column(
            Select(
                JINJA_TEMPLATE,
                id='worker_in_progress_tasks',
                item_id_getter=operator.itemgetter('taskid'),
                items='tasks',
                on_click=on_task
            )
        ),
        TO_MAIN,
        state=WorkerSG.in_progress,
        getter=task_getter
    ),
    Window(
        Const('Архив заявок:'),
        Column(
            Select(
                JINJA_TEMPLATE,
                id='worker_archive_tasks',
                item_id_getter=operator.itemgetter('taskid'),
                items='tasks',
                on_click=on_task
            )
        ),
        TO_MAIN,
        state=WorkerSG.archive,
        getter=task_getter
    ),
    Window(
        Const('Выбор объекта. Для получение объекта/объектов введите его название или хотя бы часть.'),
        MessageInput(entites_name_handler, content_types=[ContentType.TEXT]),
        SwitchTo(Const('Назад'), id='back_main', state=WorkerSG.main),
        state=WorkerSG.entities_search
    ),
    Window(
        Const('Объекты'),
        Column(
            Select(
                Format('{item[name]}'),
                id='objects',
                item_id_getter=operator.itemgetter('ent_id'),
                items='objects',
                on_click=on_entity
            )
        ),
        Back(Const('Назад')),
        state=WorkerSG.enter_object,
        getter=task_entities_getter
    ),
    Window(
        Const('Заявки на обьекте:'),
        Column(
            Select(
                JINJA_TEMPLATE,
                id='tasks',
                item_id_getter=operator.itemgetter('taskid'),
                items='tasks',
                on_click=open_tasks
            )
        ),
        Button(Const('Назад'), id='to_entity_search', on_click=to_entities),
        state=WorkerSG.tasks_entities,
        getter=tasks_open_getter

    ),
)


async def accept_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    task_service.change_status(manager.start_data['taskid'], 'в работе')

    if manager.start_data['agreement']:
        agreementer = manager.start_data['agreement']
        operatorid = config.AGREEMENTERS[agreementer]
        taskid = manager.start_data['taskid']
        await callback.answer(f'Перед работой по этой заявке нужно согласование с {agreementer}', show_alert=True)
        scheduler: AsyncIOScheduler = manager.middleware_data['scheduler']
        scheduler.add_job(agreement_alarm, 'interval', minutes=5, next_run_time=datetime.datetime.now(),
                          args=[operatorid, taskid], id=str(operatorid)+str(taskid), replace_existing=True)
    await callback.answer(f'Заявка {manager.start_data["title"]} принята в работу.')
    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)


async def onclose_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    if manager.start_data['act']:
        await manager.switch_to(WorkerTaskSG.act, show_mode=ShowMode.DELETE_AND_SEND)
    else:
        await manager.switch_to(WorkerTaskSG.media_pin, show_mode=ShowMode.DELETE_AND_SEND)


async def get_back(callback: CallbackQuery, button: Button, manager: DialogManager):
    task_service.change_status(manager.start_data['taskid'], 'в работе')
    await callback.answer(f'Заявка {manager.start_data["title"]} снова в работе.')


def is_opened(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'назначено'


def not_in_archive(data, widget, manager: DialogManager):
    return manager.start_data['status'] != 'закрыто'


def is_performed(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'выполнено'


def isnt_performed(data, widge, manager: DialogManager):
    return manager.start_data['status'] not in ('выполнено', 'закрыто')


def is_in_progress(data, widget, manager: DialogManager):
    return manager.start_data['status'] == 'в работе'


async def media_pin_task(message: Message, message_input: MessageInput, manager: DialogManager, callback=CallbackQuery):
    txt = message.caption
    media_id = message.video.file_id
    media_type = message.content_type
    task_service.save_result(txt, media_id, media_type, manager.start_data['taskid'])

    taskid = manager.start_data['taskid']
    run_date = datetime.datetime.now() + datetime.timedelta(days=3)
    scheduler: AsyncIOScheduler = manager.middleware_data['scheduler']

    task_service.change_status(taskid, 'выполнено')
    if not manager.start_data['act']:
        scheduler.add_job(close_task, trigger='date', run_date=run_date, args=[taskid], id=str(taskid),
                          replace_existing=True)

    operators = empl_service.get_employees_by_position('operator')
    for o in operators:
        operatorid = o['userid']
        slave = manager.start_data['username']
        task = manager.start_data['title']
        taskid = manager.start_data['taskid']
        scheduler.add_job(confirmed_task, 'interval', minutes=5, next_run_time=datetime.datetime.now(),
                          args=[operatorid, slave, task, taskid], id=str(operatorid) + str(taskid),
                          replace_existing=True)

    text = f'Заявка {manager.start_data["title"]} выполнена. Ожидается подтверждение закрытия от оператора или клиента.'
    mes = await message.answer(text=text)
    await asyncio.sleep(5)
    await mes.delete()
    await manager.done()


task_dialog = Dialog(
    Window(
        DynamicMedia('media', when=F['media']),
        Format('{start_data[created]}'),
        Format('{start_data[name]}'),
        Format('{start_data[title]}'),
        Format('{start_data[description]}'),
        Format('Приоритет: {start_data[priority]}'),
        Format('Статус: {start_data[status]}'),
        Jinja('Акт: {{ "да" if start_data["act"] else "нет" }}'),
        Format('\n\n<b><i><u>Согласование: {start_data[agreement]}</u></i></b>', when=F['start_data']['agreement']),
        Button(Const('Принять'), id='accept_task', on_click=accept_task, when=is_opened),
        Button(Const('Выполнено'), id='close_task', on_click=onclose_task, when=isnt_performed),
        Button(Const('Вернуть в работу'), id='back_to_work', on_click=get_back, when=is_performed),
        Button(Const('Назад'), id='cancel', on_click=on_cancel),
        state=WorkerTaskSG.main,
        getter=media_getter
    ),
    Window(
        Const('К этой заявке необходимо приложить фото акта.'),
        MessageInput(func=act_handler, content_types=[ContentType.PHOTO]),
        SwitchTo(Const('Назад'), id='to_main', state=WorkerSG.main),
        state=WorkerTaskSG.act
    ),
    Window(
        Const('Для закрытия заявки добавьте видеоотчёт.'),
        MessageInput(media_pin_task, content_types=[ContentType.VIDEO]),
        SwitchTo(Const('Назад'), id='to_main', state=WorkerSG.main),
        state=WorkerTaskSG.media_pin
    )
)
