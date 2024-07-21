import operator

from aiogram import F
from aiogram.enums import ContentType
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    Column,
    Group,
    Next,
    Radio,
    Select,
    Start,
    SwitchTo,
)
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Jinja

from db import empl_service
from . import getters, handlers, states

CANCEL_EDIT = SwitchTo(
    Const("Отменить редактирование"),
    when=F["dialog_data"]["finished"],
    id="cnl_edt",
    state=states.NewSG.preview,
)

JINJA_TEMPLATE = Jinja(
    "{% set dttm_list = item.created.split() %}"
    '{% set dt_list = dttm_list[0].split("-") %}'
    '{% set dt = dt_list[2]+"."+dt_list[1] %}'
    '{% set d = "\U0000231b" if item.status == "отложено" else "" %}'
    '{% set st = "\U00002705" if item.status == "выполнено" else "\U0001f7e9" if item.status == '
    '"в работе" else "" %}'
    '{% set sl = item.username if item.username else "\U00002753" %}'
    '{% set pr = item.priority if item.priority else "" %}'
    '{% set ob = item.name if item.name else "" %}'
    '{% set tt = item.title if item.title else "" %}'
    '{% set ag = "\U00002757\U0001f4de\U00002757" if item.agreement else "" %}'
    "{{ag}}{{d}}{{st}} {{dt}} {{pr}} {{sl}} {{ob}} {{tt}}"
)


new = Dialog(
    Window(
        Const(
            "Выбор объекта. Для получение объекта/объектов введите его название или хотя бы часть."
        ),
        MessageInput(handlers.ent_name_handler, content_types=[ContentType.TEXT]),
        Back(Const("Назад")),
        CANCEL_EDIT,
        state=NewSG.entity_choice,
    ),
    Window(
        Const("Найденные объекты:"),
        Column(
            Radio(
                Format("🔘 {item[name]}"),
                Format("⚪️ {item[name]}"),
                id="choose_entity",
                item_id_getter=lambda item: item["ent_id"],
                items="entities",
                on_click=handlers.on_entity,
            ),
        ),
        Button(
            Const("Подтвердить"), id="confirm_entity", on_click=handlers.next_or_end
        ),
        Next(Const("Продолжить без объекта")),
        Back(Const("Назад")),
        CANCEL_EDIT,
        state=states.NewSG.entities,
        getter=getters.entitites,
    ),
    Window(
        Const("Ваш номер телефона:"),
        TextInput(id="phone_input", on_success=handlers.next_or_end),
        Back(Const("Назад")),
        CANCEL_EDIT,
        Cancel(Const("Отменить создание")),
        state=states.NewSG.phone,
    ),
    Window(
        Const("Тема обращения?"),
        TextInput(id="title_input", on_success=handlers.next_or_end),
        CANCEL_EDIT,
        Back(Const("Назад")),
        Cancel(Const("Отменить создание")),
        state=states.NewSG.title,
    ),
    Window(
        Const(
            "Опишите вашу проблему. Это может быть текстовое, голосовое, видеосообщение или картинка."
        ),
        MessageInput(
            handlers.task_description_handler, content_types=[ContentType.ANY]
        ),
        Back(Const("Назад")),
        CANCEL_EDIT,
        Cancel(Const("Отменить создание")),
        state=states.NewSG.description,
    ),
    Window(
        Const("Выбор приоритета:"),
        Radio(
            Format("🔘 {item[0]}"),
            Format("⚪️ {item[0]}"),
            id="ch_prior",
            item_id_getter=operator.itemgetter(1),
            items="priorities",
            on_click=handlers.on_priority,
        ),
        Button(
            Const("Подтвердить"), id="confirm_priority", on_click=handlers.next_or_end
        ),
        Back(Const("Назад")),
        CANCEL_EDIT,
        getter=getters.priority,
        state=states.NewSG.priority,
    ),
    Window(
        Const("Необходимость акта от исполнителя:"),
        Radio(
            Format("🔘 {item[0]}"),
            Format("⚪️ {item[0]}"),
            id="act_nssr",
            item_id_getter=lambda x: x[1],
            items="act_nssr",
            on_click=handlers.on_act,
        ),
        Button(Const("Подтвердить"), id="confirm_act", on_click=handlers.next_or_end),
        Back(Const("Назад")),
        CANCEL_EDIT,
        getter=getters.acts,
        state=states.NewSG.act,
    ),
    Window(
        Const("Назначить работника"),
        Column(
            Radio(
                Format("🔘 {item[username]}"),
                Format("⚪️ {item[username]}"),
                id="choose_slave",
                item_id_getter=lambda item: item["userid"],
                items="slaves",
                on_click=handlers.on_slave,
            ),
        ),
        Button(
            Const("Убрать исполнителя"),
            id="del_performer",
            on_click=handlers.on_del_performer,
        ),
        Button(Const("Подтвердить"), id="confirm_slave", on_click=handlers.next_or_end),
        Back(Const("Назад")),
        CANCEL_EDIT,
        state=states.NewSG.performer,
        getter=getters.slaves,
    ),
    Window(
        Const("Если нужно согласование, выберите с кем:"),
        Column(
            Radio(
                Format("🔘 {item}"),
                Format("⚪️ {item}"),
                id="agreementers",
                item_id_getter=lambda item: item,
                items="agreementers",
                on_click=handlers.on_agreementer,
            )
        ),
        Button(
            Const("Подтвердить"),
            id="confirm_agreementer",
            on_click=handlers.next_or_end,
        ),
        Back(Const("Назад")),
        CANCEL_EDIT,
        state=states.NewSG.agreement,
        getter=getters.agreementers,
    ),
    Window(
        Jinja("""Ваша заявка:

        <b>Объект</b>: {{entity if entity else ''}}
        <b>Телефон</b>: {{phone if phone else ''}}
        <b>Тема</b>: {{title if title else ''}}
        <b>Описание</b>: {{description if description else ''}}
        <b>Приоритет</b>: {{priority if priority else ''}}
        <b>Работник</b>: {{username if username else ''}}
        <b>Акт</b>: {{'Да' if act else 'Нет'}}
        <b>Согласование</b>: {{agreement if agreement else ''}}
        """),
        Start(
            Const("Мультимедиа"),
            id="to_multimedia",
            state=states.MediaSG.main,
            when="media_id",
        ),
        Button(Const("Сохранить"), id="confirm_creating", on_click=handlers.on_confirm),
        SwitchTo(
            Const("Изменить объект"), id="to_entity", state=states.NewSG.entity_choice
        ),
        SwitchTo(Const("Изменить телефон"), id="to_phone", state=states.NewSG.phone),
        SwitchTo(Const("Изменить Тему"), id="to_title", state=states.NewSG.title),
        SwitchTo(
            Const("Изменить приоритет"), id="to_priority", state=states.NewSG.priority
        ),
        SwitchTo(Const("Необходимость акта"), id="to_act", state=states.NewSG.act),
        SwitchTo(
            Const("Изменить описание"),
            id="to_description",
            state=states.NewSG.description,
        ),
        SwitchTo(
            Const("Изменить исполнителя"), id="to_slave", state=states.NewSG.performer
        ),
        SwitchTo(
            Const("Необходимость согласования"),
            id="to_agreement",
            state=states.NewSG.agreement,
        ),
        Cancel(Const("Отмена")),
        state=states.NewSG.preview,
        getter=getters.result,
        parse_mode="html",
    ),
    on_start=handlers.on_start,
)


def user_is_operator(data, widget, dialog_manager: DialogManager) -> bool:
    user: dict = empl_service.get_employee(userid=dialog_manager.event.from_user.id)
    return user.get("status") == "operator"


def user_is_performer(data, widget, dialog_manager: DialogManager) -> bool:
    user: dict = empl_service.get_employee(userid=dialog_manager.event.from_user.id)
    return user.get("status") == "worker"


tasks = Dialog(
    Window(
        Format("{wintitle}"),
        Column(
            Select(
                JINJA_TEMPLATE,
                id="sel_task",
                item_id_getter=lambda x: x.get("taskid"),
                items="tasks",
                on_click=handlers.on_task
            )
        ),
        Button(Const("Обновить"), id="reload_tasks"),
        Cancel(Const("Назад")),
        state=states.TasksSG.tasks,
        getter=getters.tasks,
    ),
    Window(
        Const("Заявка: \n"),
        Format("{created}"),
        Format("Тема: {title}"),
        Format("Объект: {name}", when="name"),
        Format("Исполнитель: {username}", when="username"),
        Const("<b>Высокий приоритет!</b>", when="priority"),
        Format("Статус: {status}"),
        Format("Нужен акт", when="act"),
        Format("<b><i><u>Согласование: {agreement}</u></i></b>", when="agreement"),
        Format("\n <b>Информация по закрытию:</b> \n {summary}", when="summary"),
        Start(
            Const("Мультимедиа от оператора"),
            id="mm_description",
            state=states.MediaSG.main,
            when="media_id",
        ),
        Start(
            Const("Видео от исполнителя"),
            id="to_media",
            state=states.MediaSG.main,
            when="resultid",
        ),
        Start(Const("Акт"), id="act", state=states.MediaSG.main, when="actid"),
        Group(
            Button(
                Const("Редактировать"),
                id="edit_task",
                on_click=handlers.edit_task,
                when=(F["status"] != "закрыто"),
            ),
            Button(
                Const("Отложить"),
                id="delay_task",
                on_click=handlers.on_delay,
                when=(F["status"] != "отложено"),
            ),
            Start(Const('Переместить в архив'), id='close_task', state=None, data={'taskid'}),
            # Button(
            #     Const("Переместить в архив"),
            #     id="close_task",
            #     on_click=handlers.to_confirmation,
            #     when=(F["status"] != "закрыто"),
            # ),
            Button(
                Const("Вернуть в работу"),
                id="return_to_work",
                on_click=on_return,
                when=(F["status"] == "выполнено"),
            ),
            when=user_is_operator,
        ),
        Group(
            when=user_is_performer,
        ),
        Back(Const('Назад')),
        state=states.TaskSG.task,
        getter=getters.task,
    ),
)


media = Dialog(
    Window(
        DynamicMedia("media"),
        Cancel(Const("Назад")),
        state=states.MediaSG.main,
        getter=getters.media,
    )
)
