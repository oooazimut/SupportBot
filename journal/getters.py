from datetime import datetime
from aiogram.enums import ContentType
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from db.service import EmployeeService, JournalService, ReceiptsService


async def locations(dialog_manager: DialogManager, **kwargs):
    journal = JournalService.get_records(
        {"userid": dialog_manager.event.from_user.id, "date": datetime.today().date()}
    )
    if journal:
        journal.sort(key=lambda x: x["dttm"])
    return {"locations": ("Офис", "Дом", "Объект"), "journal": journal}


async def actions(dialog_manager: DialogManager, **kwargs):
    return {"actions": ("Приехал", "Уехал")}


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
        dialog_manager.dialog_data["receipts"] = ReceiptsService.get_receipts(
            {"dttm": rec_date, "employee": userid}
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
