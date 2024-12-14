from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from config import TasksStatuses
from db.service import task_service


async def closing_types_geter(dialog_manager: DialogManager, **kwargs):
    types = [("Сделано всё", 1), ("Сделано не всё", 0)]
    return {"closing_types": types}


async def client_tasks_exists_getter(dialog_manager: DialogManager, **kwargs):
    tasks_exists = bool(task_service.get_by_filters(status=TasksStatuses.FROM_CUSTOMER))
    return {"tasks_exists": tasks_exists}


async def description_getter(dialog_manager: DialogManager, **kwargs):
    task = dialog_manager.start_data

    media_type = task.get("media_type", "").split(",")
    media_id = task.get("media_id", "").split(",")
    index = await dialog_manager.find("summary_media_scroll").get_page()
    media = (
        MediaAttachment(media_type[index], file_id=MediaId(media_id[index]))
        if task.get("media_id")
        else None
    )
    pages = len(media_id)
    return {
        "task": task,
        "pages": pages,
        "media": media,
    }
