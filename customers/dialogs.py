from aiogram_dialog.widgets.input import TextInput
import config

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Start
from aiogram_dialog.widgets.text import Const, Jinja

from . import states, handlers
from tasks import states as task_states


main_dialog = Dialog(
    Window(
        Const('Вас приветствует бот техподдержки компании "Азимут"'),
        Button(
            Const("Создать заявку"), id="start_creating", on_click=handlers.on_new_task
        ),
        Start(
            Const("Активные заявки"),
            id="customer_tasks",
            state=task_states.TasksSG.tasks,
            data={"wintitle": config.TasksTitles.FROM_CUSTOMER},
        ),
        Start(Const("Архив"), id="customer_archive", state=task_states.TasksSG.tasks),
        state=states.CusMainSG.main,
    ),
)

new_customer = Dialog(
    Window(
        Const("Как вас зовут?"),
        TextInput(id="cust_name_input", on_success=handlers.next_or_end),
        state=states.NewCustomerSG.name,
    ),
    Window(
        Const("Ваш номер телефона?"),
        TextInput(id="cust_phone_input", on_success=handlers.next_or_end),
        state=states.NewCustomerSG.phone,
    ),
    Window(
        Const("Название объекта, на котором Вы работаете?"),
        TextInput(id="cust_object_input", on_success=handlers.next_or_end),
        state=states.NewCustomerSG.object,
    ),
    Window(
        Jinja(""""""),
        Button(Const("Подтвердить"), id="confirm_customer_creation"),
        state=states.NewCustomerSG.preview,
    ),
)
