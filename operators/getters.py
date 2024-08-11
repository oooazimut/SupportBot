from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from db.service import TaskService


async def review_getter(dialog_manager: DialogManager, **kwargs):
    task: dict = dialog_manager.dialog_data["task"].copy()
    resultmedia = None
    if task["resultid"]:
        resultmedia = MediaAttachment(
            type=task["resulttype"], file_id=MediaId(task["resultid"])
        )
    task.update({"resultmedia": resultmedia})
    return task


async def addition_getter(dialog_manager: DialogManager, **kwargs):
    task = dialog_manager.dialog_data["task"]
    media = MediaAttachment(type=task["media_type"], file_id=MediaId(task["media_id"]))
    return {"media": media}


async def act_getter(dialog_manager: DialogManager, **kwargs):
    task = dialog_manager.dialog_data["task"]
    media = MediaAttachment(type=task["acttype"], file_id=MediaId(task["actid"]))
    return {"media": media}


async def with_acts_getter(dialog_manager: DialogManager, **kwargs):
    tasks = TaskService.get_tasks_by_status(status="проверка")
    return {"tasks": tasks}


async def closingtype_getter(dialog_manager: DialogManager, **kwargs):
    task = TaskService.get_task(taskid=dialog_manager.start_data.get("taskid"))[0]
    dialog_manager.dialog_data['task'] = task
    c_types = [
        ("частично", 0),
        ("полностью", 1),
    ]

    return {
        "c_types": c_types,
    }
