import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import MyBot
from db import task_service


async def reminders_task_to_worker():
    tasks = task_service.get_task_reminder()
    bot: Bot = MyBot.get_instance()
    for task in tasks:
        messaga = await bot.send_message(chat_id=task['slave'], text='Есть заявки с высоким приоритетом!')
        await asyncio.sleep(30)
        await messaga.delete()


async def reminders_task_to_morning():
    tasks = task_service.get_task_reminder_for_morning()
    bot: Bot = MyBot.get_instance()
    for task in tasks:
        await bot.send_message(chat_id=task['slave'], text='У вас еще остались незавершенные дела')


async def close_task(taskid: int):
    task_service.change_status(taskid, 'закрыто')


class TaskFactory(CallbackData, prefix='taskfctr'):
    action: str
    task: str


async def new_task(slaveid: int, taskid: int):
    bot: Bot = MyBot.get_instance()
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Хорошо', callback_data=TaskFactory(action='get', task=str(taskid)))
    try:
        messaga = await bot.send_message(chat_id=slaveid, text='Новая заявка!', reply_markup=keyboard.as_markup())
        await asyncio.sleep(295)
        await messaga.delete()
    except TelegramBadRequest:
        pass


async def confirmed_task(operatorid, slave, title):
    bot: Bot = MyBot.get_instance()
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Хорошо', callback_data=TaskFactory(action='сonfirmed', task=title))
    try:
        messaga = await bot.send_message(chat_id=operatorid, text=f'{slave} выполнил заявку {title}.',
                                         reply_markup=keyboard.as_markup())
        await asyncio.sleep(295)
        await messaga.delete()
    except TelegramBadRequest:
        pass
