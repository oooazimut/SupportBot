from aiogram_dialog import DialogManager

from db.service import EmployeeService, JournalService


async def locations(dialog_manager: DialogManager, **kwargs):
    return {"locations": ("Офис", "Дом", "Объект")}


async def actions(dialog_manager: DialogManager, **kwargs):
    return {"actions": ("Приехал", "Уехал")}


async def users(dialog_manager: DialogManager, **kwargs):
    users = EmployeeService.get_employees()
    return {"users": users}


async def result(dialog_manager: DialogManager, **kwargs):
    def append_data(data: dict, journal: list):
        temp = JournalService.get_records(data)
        if temp:
            journal.append(temp)

    data = []
    search_data = dict()
    rec_date = dialog_manager.dialog_data.get('date')
    if rec_date:
        search_data['date'] = rec_date
    

    if dialog_manager.start_data:
        search_data['userid'] = dialog_manager.start_data.get("userid", "")
        append_data(search_data, data)
    else:
        users = EmployeeService.get_employees()
        for user in users:
            search_data['userid'] = user.get('userid')
            append_data(search_data, data)

    user_index = await dialog_manager.find("users_scroll").get_page()
    username = journal = None

    if data:
        username = data[user_index][0]["username"]
        journal = data[user_index]

    pages = len(data)
    # print(pages)

    return {"pages": pages, "username": username, "journal": journal}
