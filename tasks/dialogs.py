import config

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
    Multiselect,
    Next,
    NumberedPager,
    ScrollingGroup,
    Select,
    StubScroll,
    SwitchTo,
)
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Jinja, List
from custom.babel_calendar import CustomCalendar
from db.service import EmployeeService

from . import getters, handlers, states

CANCEL_EDIT = Cancel(
    Const("Отменить редактирование"),
    when=F["dialog_data"]["finished"],
)

PASS = Button(
    Const("Пропустить"),
    id="next_or_end",
    on_click=handlers.next_or_end,
    when=~F["dialog_data"]["finished"],
)

BACK = Button(Const("Назад"), id="back_or_back", on_click=handlers.on_back)

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
        MessageInput(handlers.ent_name_handler),
        PASS,
        BACK,
        CANCEL_EDIT,
        Cancel(Const("Отменить создание"), when=~F["dialog_data"]["finished"]),
        state=states.NewSG.entity_choice,
    ),
    Window(
        Const("Найденные объекты:"),
        Column(
            Select(
                Format("{item[name]}"),
                id="choose_entity",
                item_id_getter=lambda x: x.get("ent_id"),
                items="entities",
                on_click=handlers.on_entity,
            ),
        ),
        PASS,
        BACK,
        CANCEL_EDIT,
        Cancel(Const("Отменить создание")),
        state=states.NewSG.entities,
        getter=getters.entitites,
    ),
    Window(
        Const("Ваш номер телефона:"),
        TextInput(id="phone_input", on_success=handlers.next_or_end),
        PASS,
        BACK,
        CANCEL_EDIT,
        Cancel(Const("Отменить создание"), when=~F["dialog_data"]["finished"]),
        state=states.NewSG.phone,
    ),
    Window(
        Const("Тема обращения?"),
        TextInput(id="title_input", on_success=handlers.next_or_end),
        PASS,
        BACK,
        CANCEL_EDIT,
        Cancel(Const("Отменить создание"), when=~F["dialog_data"]["finished"]),
        state=states.NewSG.title,
    ),
    Window(
        Const(
            "Опишите вашу проблему. Это может быть текстовое, голосовое, видеосообщение или картинка."
        ),
        MessageInput(
            handlers.task_description_handler, content_types=[ContentType.ANY]
        ),
        PASS,
        BACK,
        CANCEL_EDIT,
        Cancel(Const("Отменить создание"), when=~F["dialog_data"]["finished"]),
        state=states.NewSG.description,
    ),
    Window(
        Const("Выбор приоритета:"),
        Select(
            Format("{item[0]}"),
            id="ch_prior",
            item_id_getter=lambda x: x[1],
            items="priorities",
            on_click=handlers.on_priority,
        ),
        BACK,
        CANCEL_EDIT,
        Cancel(Const("Отменить создание"), when=~F["dialog_data"]["finished"]),
        getter=getters.priority,
        state=states.NewSG.priority,
    ),
    Window(
        Const("Необходимость акта от исполнителя:"),
        Select(
            Format("{item[0]}"),
            id="act_nssr",
            item_id_getter=lambda x: x[1],
            items="act_nssr",
            on_click=handlers.on_act,
        ),
        BACK,
        CANCEL_EDIT,
        Cancel(Const("Отменить создание"), when=~F["dialog_data"]["finished"]),
        getter=getters.acts,
        state=states.NewSG.act,
    ),
    Window(
        Const("Назначить работника"),
        Column(
            Multiselect(
                Format("✓  {item[username]}"),
                Format("{item[username]}"),
                id="sel_slaves",
                item_id_getter=lambda item: item["userid"],
                items="slaves",
            ),
            Button(
                Const("Без исполнителя"),
                id="del_performer",
                on_click=handlers.on_del_performer,
                when=F["dialog_data"]["finished"],
            ),
            Button(
                Const("Подтвердить"),
                id="confirm_prf_choice",
                on_click=handlers.on_slave_choice,
            ),
            PASS,
        ),
        BACK,
        CANCEL_EDIT,
        Cancel(Const("Отменить создание"), when=~F["dialog_data"]["finished"]),
        state=states.NewSG.performer,
        getter=getters.slaves,
    ),
    Window(
        Const("Если нужно согласование, выберите с кем:"),
        Column(
            Select(
                Format("{item}"),
                id="agreementers",
                item_id_getter=lambda item: item,
                items="agreementers",
                on_click=handlers.on_agreementer,
            ),
            Button(
                Const("Без согласования"),
                id="without_agreement",
                on_click=handlers.on_without_agreement,
            ),
            PASS,
        ),
        BACK,
        CANCEL_EDIT,
        Cancel(Const("Отменить создание"), when=~F["dialog_data"]["finished"]),
        state=states.NewSG.agreement,
        getter=getters.agreementers,
    ),
    Window(
        Jinja("""Ваша заявка:

        <b>Объект</b>: {{name if name else ''}}
        <b>Телефон</b>: {{phone if phone else ''}}
        <b>Тема</b>: {{title if title else ''}}
        <b>Описание</b>: {{description if description else ''}}
        <b>Приоритет</b>: {{priority if priority else ''}}
        <b>Работник[и]</b>: {{usernames or username  or ''}}
        <b>Акт</b>: {{'Да' if act else 'Нет'}}
        <b>Согласование</b>: {{agreement if agreement else ''}}
        """),
        Button(
            Const("Мультимедиа"),
            id="to_multimedia",
            on_click=handlers.show_operator_media,
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
    user: dict = EmployeeService.get_employee(userid=dialog_manager.event.from_user.id)
    return user.get("position") == "operator"


def user_is_performer(data, widget, dialog_manager: DialogManager) -> bool:
    user = EmployeeService.get_employee(userid=dialog_manager.event.from_user.id)
    return user.get("position") == "worker"


tasks = Dialog(
    Window(
        Format("{wintitle}"),
        ScrollingGroup(
            Column(
                Select(
                    JINJA_TEMPLATE,
                    id="sel_task",
                    item_id_getter=lambda x: x.get("taskid"),
                    items="tasks",
                    on_click=handlers.on_task,
                )
            ),
            id="scroll_tasks",
            height=10,
            hide_on_single_page=True,
        ),
        Button(Const("Обновить"), id="reload_tasks"),
        Cancel(Const("Назад")),
        state=states.TasksSG.tasks,
        getter=getters.tasks,
    ),
    Window(
        Const("Заявка: \n"),
        Format("{created}"),
        Format("Объект: {name}", when="name"),
        Format("Тема: {title}"),
        Format("Описание: {description}", when="description"),
        Format("Исполнитель: {username}", when="username"),
        Const("<b>Высокий приоритет!</b>", when="priority"),
        Format("Статус: {status}"),
        Format("\nНужен акт", when="act"),
        Format("<b><i><u>Согласование: {agreement}</u></i></b>", when="agreement"),
        Button(
            Const("Мультимедиа от оператора"),
            id="mm_description",
            on_click=handlers.show_operator_media,
            when="media_id",
        ),
        Button(
            Const("Видео от исполнителя"),
            id="to_media",
            on_click=handlers.show_performer_media,
            when="resultid",
        ),
        Button(
            Const("Акт"),
            id="act",
            on_click=handlers.show_act,
            when="actid",
        ),
        Group(
            Button(
                Const("Редактировать"),
                id="edit_task",
                on_click=handlers.edit_task,
                when=F["status"].not_in(["закрыто", "проверка", "выполнено"]),
            ),
            Button(
                Const("Отложить"),
                id="delay_task",
                on_click=handlers.on_delay,
                when=F["status"].not_in(
                    ["отложено", "проверка", "закрыто", "выполнено"]
                ),
            ),
            Button(
                Const("Переместить в архив"),
                id="close_task",
                on_click=handlers.on_close,
                when=F["status"] != "закрыто",
            ),
            Button(
                Const("Вернуть в работу"),
                id="return_to_work",
                on_click=handlers.on_return,
                when=F["status"].in_(["выполнено", "закрыто", "проверка"]),
            ),
            Button(Const("Удалить заявку"), id="rm_task", on_click=handlers.on_remove),
            when=user_is_operator,
        ),
        Group(
            Button(
                Const("Принять"),
                id="accept_task",
                on_click=handlers.accept_task,
                when=F["status"] == "назначено",
            ),
            Button(
                Const("Выполнено"),
                id="perform_task",
                on_click=handlers.on_perform,
                when=F["status"].not_in(
                    ["выполнено", "закрыто", "проверка", "назначено"]
                ),
            ),
            Button(
                Const("Вернуть в работу"),
                id="back_to_work",
                on_click=handlers.get_back,
                when=F["status"] == "выполнено",
            ),
            when=user_is_performer,
        ),
        Next(Const("Журнал заявки")),
        Back(Const("Назад")),
        state=states.TasksSG.task,
        getter=getters.task,
    ),
    Window(
        Const("<b>Журнал заявки\n\n</b>"),
        List(Format("{item[dttm]}\n{item[record]}\n"), items="journal"),
        Back(Const("Назад")),
        state=states.TasksSG.journal,
        getter=getters.journal,
    ),
)


media = Dialog(
    Window(
        Format("{wintitle}"),
        DynamicMedia("media"),
        StubScroll(id="media_scroll", pages="pages"),
        NumberedPager(scroll="media_scroll", when=F["pages"] > 1),
        Cancel(Const("Назад")),
        state=states.MediaSG.main,
        getter=getters.media,
    )
)


async def on_fltr_start(data, manager: DialogManager):
    manager.dialog_data["wintitle"] = config.TasksTitles.SEARCH_RESULT.value


filtration = Dialog(
    Window(
        Const("Введите название объекта или его часть"),
        MessageInput(func=handlers.entity_search, content_types=ContentType.TEXT),
        SwitchTo(
            Const("Пропустить"),
            id="to_performer",
            state=states.FiltrationSG.performer,
        ),
        Cancel(Const("Отмена")),
        state=states.FiltrationSG.subentity,
    ),
    Window(
        Const("Найденные объекты"),
        Column(
            Select(
                Format("{item[name]}"),
                id="entity",
                item_id_getter=lambda x: x.get("ent_id"),
                items="entities",
                on_click=handlers.on_entity_fltr,
            )
        ),
        Next(Const("Пропустить")),
        Back(Const("Назад")),
        Cancel(Const("Отмена")),
        state=states.FiltrationSG.entities,
        getter=getters.entitites,
    ),
    Window(
        Const("Выбор исполнителя"),
        Column(
            Select(
                Format("{item[username]}"),
                id="performers_choice",
                item_id_getter=lambda x: x.get("userid"),
                items="slaves",
                on_click=handlers.on_performer,
            )
        ),
        Next(Const("Пропустить")),
        Back(Const("Назад")),
        Cancel(Const("Отмена")),
        state=states.FiltrationSG.performer,
        getter=getters.slaves,
    ),
    Window(
        Const("Выбор даты"),
        CustomCalendar(id="calendar", on_click=handlers.on_date),
        Next(Const("Пропустить")),
        Back(Const("Назад")),
        Cancel(Const("Отмена")),
        state=states.FiltrationSG.datestamp,
    ),
    Window(
        Const("Статус заявки"),
        Column(
            Select(
                Format("{item}"),
                id="status_choice",
                item_id_getter=lambda x: x,
                items="statuses",
                on_click=handlers.on_status,
            )
        ),
        Button(
            Const("Пропустить"), id="fltr_finished", on_click=handlers.filters_handler
        ),
        Back(Const("Назад")),
        Cancel(Const("Отмена")),
        state=states.FiltrationSG.status,
        getter=getters.statuses_getter,
    ),
    on_start=on_fltr_start,
)
