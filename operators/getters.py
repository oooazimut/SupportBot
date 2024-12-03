from aiogram_dialog import DialogManager

from config import TasksStatuses
from db.service import task_service


async def closing_types_geter(dialog_manager: DialogManager, **kwargs):
    types = [("Сделано всё", 1), ("Сделано не всё", 0)]
    return {"closing_types": types}


async def client_tasks_exists_getter(dialog_manager: DialogManager, **kwargs):
    tasks_exists = bool(task_service.get_by_filters(status=TasksStatuses.FROM_CUSTOMER))
    return {"tasks_exists": tasks_exists}
