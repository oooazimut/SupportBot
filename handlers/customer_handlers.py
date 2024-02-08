import datetime

from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button


async def task_description_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    from supp_bot import task_service
    curr_time = datetime.datetime.now()
    creator = message.from_user.full_name
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
    await message.answer('Ваша заявка принята в работу, оператор свяжется с вами в ближайшее время.')
    await manager.done()


async def customer_tasks(callback: CallbackQuery, button: Button, manager: DialogManager):
    await callback.message.answer('Открытые заявки:')
