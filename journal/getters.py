from datetime import datetime

from aiogram.enums import ContentType
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from db.service import (
    car_service,
    employee_service,
    entity_service,
    journal_service,
    receipts_service,
)


async def main_getter(dialog_manager: DialogManager, **kwargs):
    journal = journal_service.get_by_filters(
        userid=dialog_manager.event.from_user.id, date=datetime.today().date()
    )
    if journal:
        journal.sort(key=lambda x: x["dttm"])

    return {"journal": journal}


async def locations_getter(dialog_manager: DialogManager, **kwargs):
    locations = entity_service.get_home_and_office()
    last_record = journal_service.get_last_record(dialog_manager.event.from_user.id)

    if last_record and last_record.split()[-1] == "Приехал":
        curr_location = last_record.rsplit(maxsplit=1)[0]
        checked_location = entity_service.get_entity_by_name(curr_location)
        if checked_location:
            locations = [
                checked_location,
            ]
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
    last_record = journal_service.get_last_record(userid)
    curr_location = dialog_manager.dialog_data.get("curr_location")

    if curr_location:
        del actions[0]
        if rec_location not in base_locations and entity_service.get_entity_by_name(
            rec_location
        ):
            del actions[-1]
        if (
            entity_service.get_entity_by_name(curr_location)
            and curr_location not in base_locations
        ):
            actions = []

    else:
        if not last_record and rec_location == "Дом":
            del actions[0]
        else:
            del actions[-1]

    return {"actions": actions}


async def users(dialog_manager: DialogManager, **kwargs):
    users = employee_service.get_all()
    return {"users": users}


async def result(dialog_manager: DialogManager, **kwargs):
    def append_data(data: dict, journal: list):
        temp = journal_service.get_by_filters(**data)
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
        users = employee_service.get_all()
        users.sort(key=lambda x: x["username"].split()[-1])
        for user in users:
            search_data["userid"] = user.get("userid")
            append_data(search_data, data)

    user_index = await dialog_manager.find("users_scroll").get_page()
    username, journal, cars = None, None, None

    if data:
        username = data[user_index][0]["username"]
        userid = data[user_index][0]["userid"]
        dialog_manager.dialog_data.update(
            receipts=receipts_service.get_by_filters(dttm=rec_date, employee=userid),
            username=username,
        )
        journal = data[user_index]
        cars = car_service.get_pinned_cars(dttm=rec_date, user=userid)

    pages = len(data)

    return {"pages": pages, "username": username, "journal": journal, "cars": cars}


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


async def cars(dialog_manager: DialogManager, **kwargs):
    cars: dict = car_service.get_all()
    return {"cars": cars}
