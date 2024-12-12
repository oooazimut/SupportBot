from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from config import TasksStatuses, TasksTitles, AGREEMENTERS
from db.service import (
    customer_service,
    employee_service,
    entity_service,
    journal_service,
    task_service,
)


def is_employee(userid):
    return bool(employee_service.get_one(userid))


def is_customer(userid):
    return bool(customer_service.get_one(userid))


async def tasks(dialog_manager: DialogManager, **kwargs):
    wintitle = dialog_manager.start_data.get("wintitle")
    tasks = list()
    match wintitle:
        case TasksTitles.OPENED:
            if is_customer(dialog_manager.event.from_user.id):
                tasks.extend(task_service.get_by_filters(**dialog_manager.start_data))
            elif is_employee(dialog_manager.event.from_user.id):
                new_tasks = task_service.get_by_filters(status=TasksStatuses.OPENED)
                delayed_tasks = task_service.get_by_filters(
                    status=TasksStatuses.DELAYED
                )
                confirmed_tasks = task_service.get_by_filters(
                    status=TasksStatuses.PERFORMED
                )
                assigned_tasks = task_service.get_by_filters(
                    status=TasksStatuses.ASSIGNED
                )

                progress_tasks = task_service.get_by_filters(
                    status=TasksStatuses.AT_WORK
                )

                performing_tasks = task_service.get_by_filters(
                    status=TasksStatuses.PERFORMING
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
        case TasksTitles.ARCHIVE:
            if is_customer(dialog_manager.event.from_user.id):
                tasks.extend(task_service.get_by_filters(**dialog_manager.start_data))
            elif is_employee(dialog_manager.event.from_user.id):
                tasks.extend(
                    task_service.get_by_filters(
                        status=TasksStatuses.ARCHIVE,
                        userid=dialog_manager.start_data.get("userid"),
                    )
                )
                tasks.extend(task_service.get_by_filters(status=TasksStatuses.CHECKED))
        case TasksTitles.ASSIGNED:
            tasks.extend(
                task_service.get_by_filters(
                    status=TasksStatuses.ASSIGNED,
                    userid=dialog_manager.event.from_user.id,
                )
            )
        case TasksTitles.IN_PROGRESS:
            tasks.extend(
                task_service.get_by_filters(
                    status=TasksStatuses.AT_WORK,
                    userid=dialog_manager.event.from_user.id,
                )
            )
            tasks.extend(
                task_service.get_by_filters(
                    status=TasksStatuses.PERFORMING,
                    userid=dialog_manager.event.from_user.id,
                )
            )
        case TasksTitles.CHECKED:
            tasks.extend(task_service.get_by_filters(status=TasksStatuses.CHECKED))
        case TasksTitles.SEARCH_RESULT:
            tasks.extend(task_service.get_by_filters(**dialog_manager.start_data))
        case TasksTitles.FROM_CUSTOMER:
            tasks.extend(
                task_service.get_by_filters(status=TasksStatuses.FROM_CUSTOMER)
            )

    tasks.sort(key=lambda x: x["created"], reverse=True)
    return {
        "wintitle": wintitle,
        "tasks": tasks,
    }


async def task(dialog_manager: DialogManager, **kwargs):
    task = task_service.get_one(dialog_manager.dialog_data.get("taskid"))
    if task:
        task["is_employee"] = is_employee(dialog_manager.event.from_user.id)
    dialog_manager.dialog_data["task"] = task

    return task


async def priority(dialog_manager: DialogManager, **kwargs):
    priorities = [("низкий", " "), ("высокий", "\U0001f525")]
    return {"priorities": priorities}


async def acts(dialog_manager: DialogManager, **kwargs):
    act_nesessary = [("с актом", 1), ("без акта", 0)]
    return {"act_nssr": act_nesessary}


async def entitites(dialog_manager: DialogManager, **kwargs):
    entities = entity_service.get_entities_by_substr(
        dialog_manager.dialog_data.get("subentity")
    )
    return {"entities": entities}


async def slaves(dialog_manager: DialogManager, **kwargs):
    slaves = employee_service.get_by_filters(position="worker")
    return {"slaves": slaves}


async def agreementers(dialog_manager: DialogManager, **k):
    return {"agreementers": AGREEMENTERS.values()}


async def result(dialog_manager: DialogManager, **kwargs):
    data: dict = dialog_manager.dialog_data["task"]
    for key in ("phone", "title", "recom_time"):
        value = dialog_manager.find(f"{key}_input").get_value()
        default_value = 1 if key == "recom_time" else None
        data[key] = value if value != "None" else data.get(key, default_value)

    usernames = list()
    for userid in data.get("slaves", []):
        usernames.append(employee_service.get_one(userid[0]).get("username"))
    data.update(usernames=usernames)

    dialog_manager.dialog_data["finished"] = True
    return data


async def performed(dialog_manager: DialogManager, **kwargs):
    task = task_service.get_one(dialog_manager.start_data["taskid"])
    performed_counter = len(task_service.get_by_filters(status=TasksStatuses.PERFORMED))
    task.update({"counter": performed_counter})
    return task


async def media(dialog_manager: DialogManager, **kwargs):
    data = dialog_manager.start_data
    m_type, m_id = (data.get(key, "").split(",") for key in ("type", "id"))
    m_type = m_type * len(m_id) if len(m_type) == 1 else m_type
    index = await dialog_manager.find("media_scroll").get_page()
    media = MediaAttachment(m_type[index], file_id=MediaId(m_id[index]))

    return {
        "pages": len(m_id),
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
    data = journal_service.get_by_filters(
        taskid=dialog_manager.dialog_data.get("task", {}).get("taskid")
    )
    dates = list(set([item.get("dttm").split()[0] for item in data]))
    dates.sort()
    pages = len(dates)
    curr_page = await dialog_manager.find("scroll_taskjournal").get_page()

    journal = [item for item in data if dates[curr_page] in item.get("dttm")]

    return {"journal": journal, "pages": pages}


async def description_getter(dialog_manager: DialogManager, **kwargs):
    task = dialog_manager.dialog_data.get("task", {})

    media_type = task.get("media_type", "").split(",")
    media_id = task.get("media_id", "").split(",")
    index = await dialog_manager.find("description_media_scroll").get_page()
    media = (
        MediaAttachment(media_type[index], file_id=MediaId(media_id[index]))
        if task.get('media_id')
        else None
    )
    pages = len(media_id)
    return {
        "task": task,
        "pages": pages,
        "media": media,
    }
