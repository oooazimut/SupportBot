import datetime

from aiogram import F, Bot
from aiogram.enums import ContentType
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import SwitchTo, Button
from aiogram_dialog.widgets.text import Const
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import empl_service, task_service
from db.service import EntityService
from states import TaskCreating

async def reminders_task_to_worker(cls, bot: Bot, scheduler: AsyncIOScheduler, manager: DialogManager):
    tasks=task_service.get_task_reminder(params=None)
    for task in tasks:
        bot = manager.middleware_data['bot']
        await bot.send_message(chat_id=tasks['slave'], text='У вас не выполненная задача с высоким приорететом')
async def reminders_task_to_morning(cls, bot: Bot, scheduler: AsyncIOScheduler):
    tasks=task_service.get_task_reminder_for_morning(params=None)
    for task in tasks:
        await bot.send_message(chat_id=tasks['slave'], text='У вас еще остались не завершенные дела')