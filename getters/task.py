from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from db import empl_service


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
    media = MediaAttachment(mediatype, file_id=MediaId(mediaid))
    dialog_manager.dialog_data['finished'] = True
    return {
        'entity': dialog_manager.dialog_data['task'].get('name') or dialog_manager.start_data.get('name'),
        'phone': dialog_manager.find('phone_input').get_value() or dialog_manager.start_data.get('phone'),
        'title': dialog_manager.find('title_input').get_value() or dialog_manager.start_data.get('title'),
        'description': dialog_manager.dialog_data['task'].get['description'] or dialog_manager.start_data.get(
            'description'),
        'media': media
    }
