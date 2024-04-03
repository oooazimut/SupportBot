import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ContentType
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram_dialog import setup_dialogs, DialogManager, StartMode, Dialog, Window
from aiogram_dialog.api.entities import MediaAttachment
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const


class DialogSG(StatesGroup):
    first = State()
    second = State()


start_router = Router()


@start_router.message(CommandStart())
async def start_handler(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=DialogSG.first, mode=StartMode.RESET_STACK)


async def voice_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    manager.dialog_data['mediaid'] = message.voice.file_id
    manager.dialog_data['mediatype'] = message.content_type
    await manager.next()


async def getter(dialog_manager: DialogManager, **kwargs):
    media = MediaAttachment(dialog_manager.dialog_data['mediatype'], dialog_manager.dialog_data['mediaid'])
    return {
        'media': media
    }


dialog = Dialog(
    Window(
        Const('Давай уже свою голосовуху'),
        MessageInput(voice_handler, content_types=[ContentType.ANY]),
        state=DialogSG.first
    ),
    Window(
        Const('Вот твоя голосовуха'),
        DynamicMedia('media'),
        Back(Const('Назад')),
        state=DialogSG.second,
        getter=getter
    )
)


async def main():
    _logger = logging.getLogger()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    bot = Bot('6549074778:AAGsVLJrEUl_oOfpeA_Lzm-IxHD15-EH22w')
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_routers(dialog)
    setup_dialogs(dp)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
