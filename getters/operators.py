from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId


async def task_getter(dialog_manager: DialogManager, **kwargs):
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
