from aiogram_dialog import DialogManager


async def task_entities_getter(dialog_manager: DialogManager):
    objects = dialog_manager.dialog_data['entities']
    return {'objects': objects}


async def tasks_open_getter(dialog_manager: DialogManager):
    tasks_open = dialog_manager.dialog_data['task']
    return {'task': tasks_open}
