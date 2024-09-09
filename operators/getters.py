from aiogram_dialog import DialogManager


async def closing_types_geter(dialog_manager: DialogManager, **kwargs):
    types = [("Сделано всё", 1), ("Сделано не всё", 0)]
    return {"closing_types": types}
