import asyncio

from aiogram import Bot

from db import task_service


async def reminders_task_to_worker(bot: Bot):
    tasks = task_service.get_task_reminder()
    for task in tasks:
        messaga = await bot.send_message(chat_id=task['slave'], text='Есть заявки с высоким приоритетом!')
        await asyncio.sleep(30)
        await messaga.delete()


async def reminders_task_to_morning(bot: Bot):
    tasks = task_service.get_task_reminder_for_morning()
    for task in tasks:
        await bot.send_message(chat_id=task['slave'], text='У вас еще остались незавершенные дела')


async def close_task(taskid: int):
    task_service.change_status(taskid, 'закрыто')
