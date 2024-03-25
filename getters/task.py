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
    if dialog_manager.start_data:
        dialog_manager.dialog_data['task'] = dialog_manager.start_data
        dialog_manager.start_data.clear()
        return dialog_manager.dialog_data['task']
    dialog_manager.dialog_data['task'] = dict()
    mediatype = dialog_manager.dialog_data['mediatype']
    mediaid = dialog_manager.dialog_data['mediaid']
    media = MediaAttachment(mediatype, file_id=MediaId(mediaid))
    dialog_manager.dialog_data['finished'] = True

    return {
        "entity": dialog_manager.find('entity_input').get_value(),
        "phone": dialog_manager.find('phone_input').get_value(),
        "title": dialog_manager.find('title_input').get_value(),
        "description": dialog_manager.dialog_data['txt'],
        'media': media
    }
