from aiogram import Bot

from db import task_service


async def reminders_task_to_worker(bot: Bot):
    tasks = task_service.get_task_reminder(params=None)
    for task in tasks:
        await bot.send_message(chat_id=task['slave'], text='Есть заявки с высоким приоритетом!')


async def reminders_task_to_morning(bot: Bot):
    tasks = task_service.get_task_reminder_for_morning()
    for task in tasks:
        await bot.send_message(chat_id=task['slave'], text='У вас еще остались незавершенные дела')
