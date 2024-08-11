from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId


async def task_entities_getter(dialog_manager: DialogManager, **kwargs):
    objects = dialog_manager.dialog_data["entities"]
    return {"objects": objects}


async def tasks_open_getter(dialog_manager: DialogManager, **kwargs):
    tasks_open = dialog_manager.dialog_data["tasks"]
    return {"tasks": tasks_open}


async def media_getter(dialog_manager: DialogManager, **kwargs):
    media = None
    mediaid = dialog_manager.start_data["media_id"]
    if mediaid:
        mediatype = dialog_manager.start_data["media_type"]
        media = MediaAttachment(mediatype, file_id=MediaId(mediaid))
    return {"media": media}


async def closing_types_geter(dialog_manager: DialogManager, **kwargs):
    types = [("Сделано всё", 1), ("Сделано не всё", 0)]
    return {"closing_types": types}
