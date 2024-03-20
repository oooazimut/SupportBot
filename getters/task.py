from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId


async def priority_getter(dialog_manager: DialogManager, **kwargs):
    priorities = [
        ('низкий', ''),
        ('высокий', '\U0001F525')
    ]
    return {
        'priorities': priorities
    }


async def result_getter(dialog_manager: DialogManager, **kwargs):
    if dialog_manager.start_data:
        dialog_manager.dialog_data['task'] = dialog_manager.start_data
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
