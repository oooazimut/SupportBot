from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message()
async def all_messages(msg: Message):
    await msg.delete()
