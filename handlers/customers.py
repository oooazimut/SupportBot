from typing import Any

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from db import task_service
from states import CustomerSG, CustomerTaskSG


async def tasks_handler(callback: CallbackQuery, button: Button, manager: DialogManager):
    userid = str(callback.from_user.id)
    tasks = task_service.get_active_tasks(userid)
    if tasks:
        manager.dialog_data[userid] = tasks
        await manager.switch_to(CustomerSG.active_tasks)
    else:
        await callback.answer('Нет активных заявок.')


async def archive_handler(callback: CallbackQuery, button: Button, manager: DialogManager):
    userid = str(callback.from_user.id)
    bot = manager.middleware_data['bot']

    tasks = task_service.get_archive_tasks(userid)
    if tasks:
        await callback.message.answer(f'Объект: {tasks[0]["name"]}\n Закрытые заявки: ')
        for task in tasks:
            await bot.send_message(chat_id=userid, text=task['created'] + '\n' + task['title'])
            for mess_id in task['client_info'].split():
                await bot.forward_message(chat_id=userid, from_chat_id=userid, message_id=mess_id)
    else:
        await callback.answer('Архив пустой.')


async def on_task(callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    userid = str(callback.from_user.id)
    task = next((t for t in manager.dialog_data[userid] if t['taskid'] == int(item_id)), None)
    await manager.start(CustomerTaskSG.main, data=task)
