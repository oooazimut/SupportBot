from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const

from db import task_service
from db.service import EntityService


async def review_getter(dialog_manager: DialogManager, **kwargs):
    task: dict = dialog_manager.dialog_data['task'].copy()
    resultmedia = None
    if task['resultid']:
        resultmedia = MediaAttachment(type=task['resulttype'], file_id=MediaId(task['resultid']))
    task.update({'resultmedia': resultmedia})
    return task


async def addition_getter(dialog_manager: DialogManager, **kwargs):
    task = dialog_manager.dialog_data['task']
    media = MediaAttachment(type=task['media_type'], file_id=MediaId(task['media_id']))
    return {'media': media}


async def act_getter(dialog_manager: DialogManager, **kwargs):
    task = dialog_manager.dialog_data['task']
    media = MediaAttachment(type=task['acttype'], file_id=MediaId(task['actid']))
    return {'media': media}


async def with_acts_getter(dialog_manager: DialogManager, **kwargs):
    tasks = task_service.get_tasks_by_status(status='проверка')
    return {'tasks': tasks}


async def objects_getter(dialog_manager: DialogManager, **kwargs):
    objects = EntityService.get_all_entities()
    return {'objects': objects}
