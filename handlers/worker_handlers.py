from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button


async def in_progress_handler(callback: CallbackQuery, button: Button, manager: DialogManager):
    # await callback.message.delete()
    await callback.answer('Вот так')


async def archive_handler(callback: CallbackQuery, button: Button, manager: DialogManager):
    # await callback.message.delete()
    await callback.answer('Вот так')
