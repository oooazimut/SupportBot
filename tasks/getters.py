from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from config import TasksStatuses, TasksTitles, AGREEMENTERS
from db.service import EmployeeService, EntityService, JournalService, TaskService


async def tasks(dialog_manager: DialogManager, **kwargs):
    wintitle = dialog_manager.start_data.get("wintitle")
    tasks = list()
    match wintitle:
        case TasksTitles.OPENED.value:
            new_tasks = TaskService.get_tasks_by_status(TasksStatuses.OPENED.value)
            delayed_tasks = TaskService.get_tasks_by_status(TasksStatuses.DELAYED.value)
            confirmed_tasks = TaskService.get_tasks_by_status(
                TasksStatuses.PERFORMED.value
            )
            assigned_tasks = TaskService.get_tasks_by_status(
                TasksStatuses.ASSIGNED.value
            )

            progress_tasks = TaskService.get_tasks_by_status(
                TasksStatuses.AT_WORK.value
            )

            performing_tasks = TaskService.get_tasks_by_status(
                TasksStatuses.PERFORMING.value
            )

            for item in (
                confirmed_tasks,
                new_tasks,
                assigned_tasks,
                progress_tasks,
                delayed_tasks,
                performing_tasks,
            ):
                tasks.extend(item)
        case TasksTitles.ARCHIVE.value:
            tasks.extend(
                TaskService.get_tasks_by_status(
                    TasksStatuses.ARCHIVE.value,
                    userid=dialog_manager.start_data.get("userid"),
                )
            )
            tasks.extend(TaskService.get_tasks_by_status(TasksStatuses.CHECKED.value))
        case TasksTitles.ASSIGNED.value:
            tasks.extend(
                TaskService.get_tasks_by_status(
                    TasksStatuses.ASSIGNED.value,
                    userid=dialog_manager.event.from_user.id,
                )
            )
        case TasksTitles.IN_PROGRESS.value:
            tasks.extend(
                TaskService.get_tasks_by_status(
                    TasksStatuses.AT_WORK.value,
                    userid=dialog_manager.event.from_user.id,
                )
            )
        case TasksTitles.CHECKED.value:
            tasks.extend(TaskService.get_tasks_by_status(TasksStatuses.CHECKED.value))
        case TasksTitles.ENTITY.value:
            data = TaskService.get_tasks_for_entity(
                dialog_manager.start_data.get("entid")
            )
            if data:
                tasks.extend(data)
                wintitle = wintitle.format(data[0].get("name", ""))
        case TasksTitles.SEARCH_RESULT.value:
            tasks.extend(TaskService.get_tasks_with_filters(dialog_manager.start_data))

    tasks.sort(key=lambda x: x["created"], reverse=True)
    return {
        "wintitle": wintitle,
        "tasks": tasks,
    }


async def task(dialog_manager: DialogManager, **kwargs):
    task = TaskService.get_task(dialog_manager.dialog_data.get("taskid"))[0]
    dialog_manager.dialog_data["task"] = task
    return task


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
    return {"agreementers": AGREEMENTERS.values()}


async def result(dialog_manager: DialogManager, **kwargs):
    data: dict = dialog_manager.dialog_data["task"]
    phone = dialog_manager.find("phone_input").get_value()
    data["phone"] = phone if phone != "None" else data.get("phone", None)
    title = dialog_manager.find("title_input").get_value()
    data["title"] = title if title != "None" else data.get("title", None)
    recom_time = dialog_manager.find("recom_time_input").get_value()
    data["recom_time"] = (
        recom_time if recom_time != "None" else data.get("recom_time", 1)
    )
    usernames = list()
    for userid in data.get("slaves", []):
        usernames.append(EmployeeService.get_employee(userid[0]).get("username"))
    data["usernames"] = usernames

    dialog_manager.dialog_data["task"] = data
    dialog_manager.dialog_data["finished"] = True
    return data


async def performed(dialog_manager: DialogManager, **kwargs):
    task = TaskService.get_task(dialog_manager.start_data["taskid"])[0]
    performed_counter = len(TaskService.get_tasks_by_status("выполнено"))
    task.update({"counter": performed_counter})
    return task


async def media(dialog_manager: DialogManager, **kwargs):
    m_type = dialog_manager.start_data.get("type", "")
    m_ids = dialog_manager.start_data.get("id", [])
    pages = len(m_ids)
    index = await dialog_manager.find("media_scroll").get_page()

    if isinstance(m_type, list):
        media = MediaAttachment(m_type[index], file_id=MediaId(m_ids[index]))
    else:
        media = MediaAttachment(m_type, file_id=MediaId(m_ids[index]))

    return {
        "pages": pages,
        "media": media,
        "wintitle": dialog_manager.start_data.get("wintitle"),
    }


async def statuses_getter(dialog_manager: DialogManager, **kwargs):
    return {
        "statuses": (
            "открыто",
            "назначено",
            "в работе",
            "выполнено",
            "проверка",
            "закрыто",
            "отложено",
        )
    }


async def journal_getter(dialog_manager: DialogManager, **kwargs):
    data = JournalService.get_records(
        taskid=dialog_manager.dialog_data.get("task", {}).get("taskid")
    )
    dates = list(set([item.get("dttm").split()[0] for item in data]))
    dates.sort()
    pages = len(dates)
    curr_page = await dialog_manager.find("scroll_taskjournal").get_page()

    journal = [item for item in data if dates[curr_page] in item.get("dttm")]

    return {"journal": journal, "pages": pages}
