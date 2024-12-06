from aiogram import F
from aiogram.types import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    Group,
    Next,
    NumberedPager,
    Start,
    StubScroll,
    SwitchTo,
)
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Jinja

from . import getters, handlers, states

main_dialog = Dialog(
    Window(
        Const('Вас приветствует бот техподдержки компании "Азимут"'),
        Button(
            Const("Создать заявку"), id="start_creating", on_click=handlers.on_new_task
        ),
        Button(
            Const("Активные заявки"),
            id="customer_tasks",
            on_click=handlers.on_current_tasks,
        ),
        Button(
            Const("Архив"), id="customer_archive", on_click=handlers.on_customer_archive
        ),
        state=states.CusMainSG.main,
    ),
)

new_customer = Dialog(
    Window(
        Const("Как вас зовут?"),
        TextInput(id="cust_name_input", on_success=handlers.next_or_end),
        Cancel(Const("Отмена")),
        state=states.NewCustomerSG.name,
    ),
    Window(
        Const("Ваш номер телефона?"),
        TextInput(id="cust_phone_input", on_success=handlers.next_or_end),
        Back(Const("Назад")),
        Cancel(Const("Отмена")),
        state=states.NewCustomerSG.phone,
    ),
    Window(
        Const("Название объекта, на котором Вы работаете?"),
        TextInput(id="cust_object_input", on_success=handlers.next_or_end),
        Back(Const("Назад")),
        Cancel(Const("Отмена")),
        state=states.NewCustomerSG.object,
    ),
    Window(
        Jinja("""Ваши данные:

<b>Имя</b>: {{ name or ''}}
<b>Телефон</b>: {{ phone or '' }}
<b>Объект</b>: {{ object or '' }}
        """),
        Button(
            Const("Подтвердить"),
            id="confirm_customer_creation",
            on_click=handlers.on_confirm_customer_creating,
        ),
        SwitchTo(
            Const("Изменить имя"),
            id="to_customer_name",
            state=states.NewCustomerSG.name,
        ),
        SwitchTo(
            Const("Изменить номер телефона"),
            id="to_customer_phone",
            state=states.NewCustomerSG.phone,
        ),
        SwitchTo(
            Const("Изменить название объекта"),
            id="to_customer_object",
            state=states.NewCustomerSG.object,
        ),
        Cancel(Const("Отмена")),
        state=states.NewCustomerSG.preview,
        getter=getters.customer_preview_getter,
    ),
)

new_task = Dialog(
    Window(
        Const("Ваша заявка:\n"),
        Format("{task[description]}", when=F["task"]["description"]),
        Const(
            "\n<b>Подсказка</b>: <i>Добавляйте текст, видео, картинки - что угодно,"
            "КРОМЕ КРУЖОЧКОВ И ГОЛОСОВЫХ! Добавлять можно неограниченное количество раз.</i>"
        ),
        DynamicMedia("media", when=F["task"]["media_id"]),
        StubScroll(id="customer_video_scroll", pages="pages"),
        Group(
            NumberedPager(scroll="customer_video_scroll", when=F["pages"] > 1), width=8
        ),
        MessageInput(
            func=handlers.description_handler,
            content_types=[
                ContentType.TEXT,
                ContentType.VIDEO,
                ContentType.AUDIO,
                ContentType.DOCUMENT,
                ContentType.PHOTO,
            ],
        ),
        Button(
            Const("Сохранить и отправить"),
            id="confirm_customer_task_creating",
            on_click=handlers.on_confirm_customer_task_creating,
        ),
        Cancel(Const("Отмена")),
        state=states.NewTaskSG.preview,
        getter=getters.task_preview_getter,
    ),
)
