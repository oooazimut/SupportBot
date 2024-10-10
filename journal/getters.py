from datetime import datetime
from typing import Any
from aiogram.enums import ContentType
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from redis.asyncio.client import Redis

from config import TasksStatuses
from db.service import (
    EmployeeService,
    EntityService,
    JournalService,
    ReceiptsService,
    TaskService,
)


async def main_getter(dialog_manager: DialogManager, **kwargs):
    journal = JournalService.get_records(
        userid=dialog_manager.event.from_user.id, date=datetime.today().date()
    )
    if journal:
        journal.sort(key=lambda x: x["dttm"])

    return {"journal": journal}


async def locations_getter(dialog_manager: DialogManager, **kwargs):
    locations = EntityService.get_home_and_office()
    last_record = JournalService.get_last_record(dialog_manager.event.from_user.id)

    if last_record and last_record.split()[-1] == "Приехал":
        curr_location = last_record.rsplit(maxsplit=1)[0]
        checked_location = EntityService.get_entity_by_name(curr_location)
        if checked_location:
            locations = checked_location
        else:
            locations = [{"ent_id": "0", "name": curr_location}]
        dialog_manager.dialog_data["curr_location"] = curr_location
        return {"locations": locations}

    return {"locations": locations}


async def actions(dialog_manager: DialogManager, **kwargs):
    actions = ["Приехал", "Уехал"]
    base_locations = ["Дом", "Офис"]
    rec_location = dialog_manager.dialog_data.get("location")
    userid = dialog_manager.event.from_user.id
    last_record = JournalService.get_last_record(userid)
    curr_location = dialog_manager.dialog_data.get("curr_location")

    if curr_location:
        del actions[0]
        if rec_location not in base_locations and EntityService.get_entity_by_name(
            rec_location
        ):
            del actions[-1]
        if EntityService.get_entity_by_name(curr_location) and curr_location not in base_locations:
            actions = []
        
    else:
        if not last_record and rec_location == "Дом":
            del actions[0]
        else:
            del actions[-1]

    return {"actions": actions}


async def users(dialog_manager: DialogManager, **kwargs):
    users = EmployeeService.get_employees()
    return {"users": users}


async def result(dialog_manager: DialogManager, **kwargs):
    def append_data(data: dict, journal: list):
        temp = JournalService.get_records(**data)
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
        dialog_manager.dialog_data["receipts"] = ReceiptsService.get_receipts(
            {
                "dttm": rec_date,
                "employee": userid,
            }
        )
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
