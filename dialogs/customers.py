import operator

from aiogram import F
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.kbd import Start, Cancel, Back, Button, Select, Column
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Jinja

from handlers.customers import on_task, tasks_handler, archive_handler
from states import TaskCreating, CustomerSG, CustomerTaskSG


async def tasks_getter(dialog_manager: DialogManager, **kwargs):
    userid = str(dialog_manager.middleware_data['event_from_user'].id)
    tasks = dialog_manager.dialog_data[userid]
    return {'tasks': tasks}


main_dialog = Dialog(
    Window(
        Const('Вас приветствует бот технической поддержки компании "Азимут"'),
        Start(Const('Создать заявку'), id='start_creating', state=TaskCreating.sub_entity),
        Button(Const('Активные заявки'), id='customer_tasks', on_click=tasks_handler),
        Button(Const('Архив'), id='customer_archive', on_click=archive_handler),
        state=CustomerSG.main,
    ),
    Window(
        Format('{tasks[0][name]}'),
        Column(
            Select(
                Format('{item[title]} {item[priority]}'),
                id='customer_active_tasks',
                item_id_getter=operator.itemgetter('taskid'),
                items='tasks',
                on_click=on_task
            )
        ),
        Back(Const('Назад')),
        state=CustomerSG.active_tasks,
        getter=tasks_getter
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
