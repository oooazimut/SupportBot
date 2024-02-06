from aiogram.types import Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput

from functions.db.write import save_task


async def task_description_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    title = manager.find('entity_input').get_value() + ': ' + manager.find('title_input').get_value()
    phone = manager.find('phone_input').get_value()
    description = message.message_id
    taskid = save_task(title=title, description=description, phone=phone)
    await message.answer(f'Ваша заявка  под номером {taskid} принята в работу, оператор свяжется с вами в ближайшее время.')
    await manager.done()
    await manager.done()
