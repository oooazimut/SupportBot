from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from db import task_service


class Getters:
    @staticmethod
    async def review(dialog_manager: DialogManager, **kwargs):
        task: dict = dialog_manager.dialog_data["task"].copy()
        resultmedia = None
        if task["resultid"]:
            resultmedia = MediaAttachment(
                type=task["resulttype"], file_id=MediaId(task["resultid"])
            )
        task.update({"resultmedia": resultmedia})
        return task

    @staticmethod
    async def addition(dialog_manager: DialogManager, **kwargs):
        task = dialog_manager.dialog_data["task"]
        media = MediaAttachment(
            type=task["media_type"], file_id=MediaId(task["media_id"])
        )
        return {"media": media}

    @staticmethod
    async def act(dialog_manager: DialogManager, **kwargs):
        task = dialog_manager.dialog_data["task"]
        media = MediaAttachment(type=task["acttype"], file_id=MediaId(task["actid"]))
        return {"media": media}

    @staticmethod
    async def with_acts(dialog_manager: DialogManager, **kwargs):
        tasks = task_service.get_tasks_by_status(status="проверка")
        return {"tasks": tasks}
