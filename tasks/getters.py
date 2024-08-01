from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from config import TasksStatuses, TasksTitles, AGREEMENTERS
from db.service import EmployeeService, EntityService, TaskService


async def tasks(dialog_manager: DialogManager, **kwargs):
    wintitle = dialog_manager.start_data.get("wintitle")
    tasks = list()
    match wintitle:
        case TasksTitles.OPENED:
            new_tasks = TaskService.get_tasks_by_status(TasksStatuses.OPENED)
            delayed_tasks = TaskService.get_tasks_by_status(TasksStatuses.DELAYED)
            confirmed_tasks = TaskService.get_tasks_by_status(TasksStatuses.CONFIRMED)
            assigned_tasks = sorted(
                TaskService.get_tasks_by_status(TasksStatuses.ASSIGNED),
                key=lambda x: x["priority"] if x["priority"] else "",
            )
            progress_tasks = sorted(
                TaskService.get_tasks_by_status(TasksStatuses.AT_WORK),
                key=lambda x: x["priority"] if x["priority"] else "",
            )
            for item in (
                delayed_tasks,
                progress_tasks,
                assigned_tasks,
                new_tasks,
                confirmed_tasks,
            ):
                tasks.extend(item)
        case TasksTitles.ARCHIVE:
            tasks.extend(TaskService.get_tasks_by_status(TasksStatuses.ARCHIVE))
        case TasksTitles.ASSIGNED:
            tasks.extend(
                TaskService.get_tasks_by_status(
                    TasksStatuses.ASSIGNED, userid=dialog_manager.event.from_user.id
                )
            )
        case TasksTitles.AT_WORK:
            tasks.extend(
                TaskService.get_tasks_by_status(
                    TasksStatuses.AT_WORK, userid=dialog_manager.event.from_user.id
                )
            )
        case TasksTitles.CHECKED:
            tasks.extend(TaskService.get_tasks_by_status(TasksStatuses.CHECKED))
    return {
        "wintitle": wintitle,
        "tasks": tasks,
    }


async def task(dialog_manager: DialogManager, **kwargs):
    task = TaskService.get_task(dialog_manager.dialog_data.get("taskid"))
    dialog_manager.dialog_data["task"] = task
    return {
        "task": task,
    }


async def priority(dialog_manager: DialogManager, **kwargs):
    priorities = [("низкий", " "), ("высокий", "\U0001f525")]
    return {"priorities": priorities}


async def acts(dialog_manager: DialogManager, **kwargs):
    act_nesessary = [("с актом", 1), ("без акта", 0)]
    return {"act_nssr": act_nesessary}


async def entitites(dialog_manager: DialogManager, **kwargs):
    entities = EntityService.get_entities_by_substr(
        dialog_manager.dialog_data.get("subentity")
    )
    return {"entities": entities}


async def slaves(dialog_manager: DialogManager, **kwargs):
    slaves = EmployeeService.get_employees_by_position("worker")
    return {"slaves": slaves}


async def agreementers(dialog_manager: DialogManager, **k):
    return {"agreementers": AGREEMENTERS}


async def result(dialog_manager: DialogManager, **kwargs):
    data: dict = dialog_manager.dialog_data["task"]
    phone = dialog_manager.find("phone_input").get_value()
    if phone != "None":
        data["phone"] = phone
    title = dialog_manager.find("title_input").get_value()
    if title != "None":
        data["title"] = title
    dialog_manager.dialog_data["task"] = data
    dialog_manager.dialog_data["finished"] = True
    return data


async def performed(dialog_manager: DialogManager, **kwargs):
    task = TaskService.get_task(dialog_manager.start_data["taskid"])[0]
    performed_counter = len(TaskService.get_tasks_by_status("выполнено"))
    task.update({"counter": performed_counter})
    return task


async def media(dialog_manager: DialogManager, **kwargs):
    m_type = dialog_manager.start_data.get("type")
    m_id = dialog_manager.start_data.get("id")
    media = MediaAttachment(m_type, file_id=MediaId(m_id))
    return {"media": media}
