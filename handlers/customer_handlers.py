import datetime

from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button

from db import task_service


async def task_description_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    curr_time = datetime.datetime.now().replace(microsecond=0)
    creator = message.from_user.id
    phone = manager.find('phone_input').get_value()
    title = manager.find('entity_input').get_value() + ': ' + manager.find('title_input').get_value()
    client_info = message.message_id
    status = 'открыто'
    priority = ''
    params = [
        curr_time,
        creator,
        phone,
        title,
        client_info,
        status,
        priority
    ]
    task_service.save_task(params=params)
    await message.answer('Ваша заявка принята в обработку и скоро появится в списке ваших заявок.')
    await manager.done()


async def tasks_handler(callback: CallbackQuery, button: Button, manager: DialogManager):
    # await callback.message.delete()
    bot = manager.middleware_data['bot']
    userid = callback.from_user.id
    tasks = task_service.get_active_tasks(userid)
    if tasks:
        await callback.message.answer(f'Объект: {tasks[0]["name"]}\n Открытые заявки:')
        for task in tasks:
            await bot.send_message(chat_id=userid, text=task['created'] + '\n' + task['title'])
            for mess_id in task['client_info'].split():
                await bot.forward_message(chat_id=userid, from_chat_id=userid, message_id=mess_id)
        manager.show_mode = ShowMode.SEND
    else:
        await callback.answer('Нет активных заявок.')


async def archive_handler(callback: CallbackQuery, button: Button, manager: DialogManager):
    userid = callback.from_user.id
    bot = manager.middleware_data['bot']

    tasks = task_service.get_archive_tasks(userid)
    if tasks:
        await callback.message.answer(f'Объект: {tasks[0]["name"]}\n Закрытые заявки: ')
        for task in tasks:
            await bot.send_message(chat_id=userid, text=task['created'] + '\n' + task['title'])
            for mess_id in task['client_info'].split():
                await bot.forward_message(chat_id=userid, from_chat_id=userid, message_id=mess_id)
        manager.show_mode = ShowMode.SEND
    else:
        await callback.answer('Архив пустой.')
