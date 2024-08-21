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
    if dialog_manager.start_data:
        dialog_manager.dialog_data['userid'] = dialog_manager.start_data.get('userid')
    journal = JournalService.get_records(dialog_manager.dialog_data)
    return {"journal": journal}
