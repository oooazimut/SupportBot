import datetime

from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button

from db import task_service


async def task_description_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    curr_time = datetime.datetime.now()
    creator = message.from_user.id
    phone = manager.find('phone_input').get_value()
    title = manager.find('entity_input').get_value() + ': ' + manager.find('title_input').get_value()
    description = message.message_id
    status = 'opened'
    priority = 'low'
    params = [
        curr_time,
        creator,
        phone,
        title,
        description,
        status,
        priority
    ]
    task_service.save_task(params=params)
    await message.answer('Ваша заявка принята в обработку и скоро появится в списке ваших заявок.')
    await manager.done()


async def tasks_handler(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.delete()
    bot = manager.middleware_data['bot']
    userid = callback.from_user.id
    # user = await bot.get_chat_member(chat_id=callback.from_user.id, user_id=callback.from_user.id)
    # print(user.user.username)
    tasks = task_service.get_active_tasks(userid)
    if tasks:
        await callback.message.answer(f'Объект: {tasks[0]["name"]}\n Открытые заявки:')
        for task in tasks:
            await bot.send_message(chat_id=userid, text=task['created'].strftime('%x : %X') + '\n' + task['title'])
            await bot.forward_message(chat_id=userid, from_chat_id=userid, message_id=task['description'])
    else:
        await callback.message.answer('Нет активных заявок.')


async def archive_handler(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.delete()
    userid = callback.from_user.id
    bot = manager.middleware_data['bot']

    tasks = task_service.get_archive_tasks(userid=userid)
    if tasks:
        await callback.message.answer(f'Объект: {tasks[0]["name"]}\n Закрытые заявки: ')
        for task in tasks:
            await bot.send_message(chat_id=userid, text=task['created'].strftime('%x : %X') + '\n' + task['title'])
            await bot.forward_message(chat_id=userid, from_chat_id=userid, message_id=task['description'])
    else:
        await callback.message.answer('Архив пустой.')
