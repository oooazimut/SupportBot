from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from db import empl_service, task_service


async def priority_getter(dialog_manager: DialogManager, **kwargs):
    priorities = [
        ('низкий', ''),
        ('высокий', '\U0001F525')
    ]
    return {
        'priorities': priorities
    }


async def entitites_getter(dialog_manager: DialogManager, **kwargs):
    entities = dialog_manager.dialog_data['entities']
    return {
        'entities': entities
    }


async def slaves_getter(dialog_manager: DialogManager, **kwargs):
    slaves = empl_service.get_employees_by_position('worker')
    return {
        'slaves': slaves
    }


async def result_getter(dialog_manager: DialogManager, **kwargs):
    mediatype = dialog_manager.dialog_data['task'].get('media_type') or dialog_manager.start_data.get('media_type')
    mediaid = dialog_manager.dialog_data['task'].get('media_id') or dialog_manager.start_data.get('media_id')
    if mediatype and mediaid:
        media = MediaAttachment(mediatype, file_id=MediaId(mediaid))
    else:
        media = None
    entity = dialog_manager.dialog_data['task'].get('name') or dialog_manager.start_data.get('name')
    phone = dialog_manager.find('phone_input').get_value()
    if phone == 'None':
        phone = dialog_manager.start_data.get('phone')
    title = dialog_manager.find('title_input').get_value()
    if title == 'None':
        title = dialog_manager.start_data.get('title')
    description = dialog_manager.dialog_data['task'].get('description') or dialog_manager.start_data.get('description')
    priority = dialog_manager.dialog_data['task'].get('priority') or dialog_manager.start_data.get('priority')
    username = dialog_manager.dialog_data['task'].get('username') or dialog_manager.start_data.get('username')
    dialog_manager.dialog_data['finished'] = True
    dialog_manager.dialog_data['to_save'] = {
        'entity': entity,
        'phone': phone,
        'title': title,
        'description': description,
        'priority': priority,
        'username': username,
    }
    return dialog_manager.dialog_data['to_save'].update({'media': media})


async def performed_getter(dialog_manager: DialogManager, **kwargs):
    task = task_service.get_task(dialog_manager.start_data['taskid'])[0]
    return task
