from datetime import datetime
from typing import Any
from aiogram.enums import ContentType
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from config import TasksStatuses
from db.service import (
    EmployeeService,
    EntityService,
    JournalService,
    ReceiptsService,
    TaskService,
)


async def main_getter(dialog_manager: DialogManager, **kwargs):
    data = {
        "userid": dialog_manager.event.from_user.id,
        "date": datetime.today().date(),
    }

    journal = JournalService.get_records(data)
    if journal:
        journal.sort(key=lambda x: x["dttm"])

    return {"journal": journal}


async def locations_getter(dialog_manager: DialogManager, **kwargs):
    data: dict[str, Any] = {"userid": dialog_manager.event.from_user.id}
    locations = EntityService.get_home_and_office()
    tasks = []

    for i in [
        TasksStatuses.ASSIGNED.value,
        TasksStatuses.AT_WORK.value,
        TasksStatuses.PERFORMED.value,
    ]:
        data["status"] = i
        temp = TaskService.get_tasks_with_filters(data) or []
        tasks.extend(temp)

    objects = [{"ent_id": i["ent_id"], "name": i["name"]} for i in tasks]
    locations.extend(objects)

    return {"locations": locations}


async def actions(dialog_manager: DialogManager, **kwargs):
    actions = ["Приехал", "Уехал"]
    home_and_office = [loc["name"] for loc in EntityService.get_home_and_office()]
    if dialog_manager.dialog_data["location"] not in home_and_office:
        actions.pop()

    return {"actions": actions}


async def users(dialog_manager: DialogManager, **kwargs):
    users = EmployeeService.get_employees()
    return {"users": users}


async def result(dialog_manager: DialogManager, **kwargs):
    def append_data(data: dict, journal: list):
        temp = JournalService.get_records(data)
        if temp:
            journal.append(sorted(temp, key=lambda x: x["dttm"]))

    data = []
    search_data = dict()
    rec_date = dialog_manager.dialog_data.get("date")
    if rec_date:
        search_data["date"] = rec_date

    if dialog_manager.start_data:
        search_data["userid"] = dialog_manager.start_data.get("userid", "")
        append_data(search_data, data)
    else:
        users = EmployeeService.get_employees()
        users.sort(key=lambda x: x["username"].split()[-1])
        for user in users:
            search_data["userid"] = user.get("userid")
            append_data(search_data, data)

    user_index = await dialog_manager.find("users_scroll").get_page()
    username = journal = None

    if data:
        username = data[user_index][0]["username"]
        userid = data[user_index][0]["userid"]
        dialog_manager.dialog_data["receipts"] = ReceiptsService.get_receipts({
            "dttm": rec_date,
            "employee": userid,
        })
        dialog_manager.dialog_data["username"] = username
        journal = data[user_index]

    pages = len(data)

    return {"pages": pages, "username": username, "journal": journal}


async def receipts_getter(dialog_manager: DialogManager, **kwargs):
    pages = len(dialog_manager.dialog_data["receipts"])
    curr_page = await dialog_manager.find("receipts_scroll").get_page()
    media = MediaAttachment(
        ContentType.PHOTO,
        file_id=MediaId(
            file_id=dialog_manager.dialog_data["receipts"][curr_page]["receipt"]
        ),
    )
    caption = dialog_manager.dialog_data["receipts"][curr_page]["caption"]

    return {
        "pages": pages,
        "media": media,
        "username": dialog_manager.dialog_data["username"],
        "caption": caption,
    }
