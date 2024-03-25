from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.manager import manager


async def task_entities_getter(dialog_manager: DialogManager):
    objects=dialog_manager.dialog_data['entities']
    return{'objects':objects}
