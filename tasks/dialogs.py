from datetime import datetime
from typing import Dict

from aiogram import F
from aiogram.enums import ContentType
from aiogram_dialog import Dialog, DialogManager, SubManager, Window
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    Checkbox,
    Column,
    Group,
    ListGroup,
    ManagedCheckbox,
    Next,
    NumberedPager,
    Radio,
    Row,
    ScrollingGroup,
    Select,
    StubScroll,
    SwitchTo,
    Url,
)
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Jinja, List

import config
from custom.babel_calendar import CustomCalendar
from db.service import employee_service, journal_service

from . import getters, handlers, states

CANCEL_EDIT = Cancel(
    Const("Отменить редактирование"),
    when=F["dialog_data"]["finished"],
)

CANCEL_CREATING = Cancel(
    Const("Отменить редактирование"),
    when=~F["dialog_data"]["finished"],
)


NEXT = Button(
    Const("Далее"),
    id="next_or_end",
    on_click=handlers.next_or_end,
    when=~F["dialog_data"]["finished"],
)

BACK = Button(Const("Назад"), id="back_or_back", on_click=handlers.on_back)

JINJA_TEMPLATE = Jinja(
    "{% set dttm_list = item.created.split() %}"
    '{% set dt_list = dttm_list[0].split("-") %}'
    '{% set dt = dt_list[2]+"."+dt_list[1] %}'
    '{% set d = "\U0000231b" if item.status == data.statuses.DELAYED else "" %}'
    '{% set st = "\U00002705" if item.status == data.statuses.PERFORMED else "\U0001f7e9" if item.status == '
    'data.statuses.AT_WORK else "" %}'
    '{% set sl = item.username or "\U00002753" %}'
    '{% set pr = item.priority or "" %}'
    '{% set ob = item.name or "" %}'
    '{% set tt = item.title or "" %}'
    '{% set ag = "\U00002757\U0001f4de\U00002757" if item.agreement else "" %}'
    '{% set vid = "\U0001f39e" if item.resultid else "" %}'
    '{% set load = "\U0001f504" if item.status == data.statuses.PERFORMING else "" %}'
    "{{load}}{{vid}}{{ag}}{{d}}{{st}} {{dt}} {{pr}} {{sl}} {{ob}} {{tt}}"
)


def when_checked(data: Dict, widget, manager: SubManager) -> bool:
    # manager for our case is already adapted for current ListGroup row
    # so `.find` returns widget adapted for current row
    # if you need to find widgets outside the row, use `.find_in_parent`
    check: ManagedCheckbox = manager.find("sel_slaves")
    return check.is_checked()


new = Dialog(
    Window(
        Const(
            "Выбор объекта. Для получение объекта/объектов введите его название или хотя бы часть."
        ),
        MessageInput(handlers.ent_name_handler),
        NEXT,
        BACK,
        CANCEL_EDIT,
        CANCEL_CREATING,
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
        NEXT,
        BACK,
        CANCEL_EDIT,
        CANCEL_CREATING,
        state=states.NewSG.entities,
        getter=getters.entitites,
    ),
    Window(
        Const("Ваш номер телефона:"),
        TextInput(id="phone_input", on_success=handlers.next_or_end),
        NEXT,
        BACK,
        CANCEL_EDIT,
        CANCEL_CREATING,
        state=states.NewSG.phone,
    ),
    Window(
        Const("Тема обращения?"),
        TextInput(id="title_input", on_success=handlers.next_or_end),
        NEXT,
        BACK,
        CANCEL_EDIT,
        CANCEL_CREATING,
        state=states.NewSG.title,
    ),
    Window(
        Const(
            "<i>Добавление описания(текст, фото, видео, документы -"
            "всё, КРОМЕ ГОЛОСОВЫХ И КРУЖОЧКОВ)</i>\n\n"
        ),
        Format(
            "<b>Описание</b>:\n{task[description]}",
            when=F["task"]["description"],
        ),
        DynamicMedia("media", when=F["task"]["media_id"]),
        StubScroll(id="description_media_scroll", pages="pages"),
        Group(
            NumberedPager(scroll="description_media_scroll", when=F["pages"] > 1),
            width=8,
        ),
        MessageInput(
            handlers.task_description_handler,
            content_types=[
                ContentType.TEXT,
                ContentType.PHOTO,
                ContentType.VIDEO,
                ContentType.AUDIO,
                ContentType.DOCUMENT,
            ],
        ),
        NEXT,
        BACK,
        CANCEL_EDIT,
        CANCEL_CREATING,
        state=states.NewSG.description,
        getter=getters.description_getter,
    ),
    Window(
        Const("Рекомендованное время выполнения заявки (в часах):"),
        TextInput(id="recom_time_input", on_success=handlers.next_or_end),
        NEXT,
        BACK,
        CANCEL_CREATING,
        CANCEL_EDIT,
        state=states.NewSG.recom_time,
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
        CANCEL_CREATING,
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
        CANCEL_CREATING,
        getter=getters.acts,
        state=states.NewSG.act,
    ),
    Window(
        Const("Назначить работника"),
        ListGroup(
            Checkbox(
                Format("✓  {item[username]}"),
                Format("{item[username]}"),
                id="sel_slaves",
            ),
            Row(
                Radio(
                    Format("🔘 {item}"),
                    Format("⚪️ {item}"),
                    id="prim_slave",
                    item_id_getter=str,
                    items=["гл", "пом"],
                    when=when_checked,
                ),
            ),
            id="lg",
            item_id_getter=lambda item: item["userid"],
            items=F["slaves"],
        ),
        Button(
            Const("Без исполнителя"),
            id="del_performer",
            on_click=handlers.on_del_performer,
            when=F["dialog_data"]["finished"],
        ),
        Button(
            Const("Подтвердить/Пропустить"),
            id="confirm_prf_choice",
            on_click=handlers.on_slave_choice,
        ),
        BACK,
        CANCEL_EDIT,
        CANCEL_CREATING,
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
        ),
        BACK,
        CANCEL_EDIT,
        CANCEL_CREATING,
        state=states.NewSG.agreement,
        getter=getters.agreementers,
    ),
    Window(
        Jinja("""
<b>Ваша заявка:</b>
<b>Объект</b>: {{name or ''}}
<b>Телефон</b>: {{phone or ''}}
<b>Тема</b>: {{title or ''}}
<b>Описание</b>: {{description or ''}}
<b>Расчетное время</b>: {{recom_time or '?'}}ч.
<b>Приоритет</b>: {{priority or ''}}
<b>Работник[и]</b>: {{usernames or username  or ''}}
<b>Акт</b>: {{'Да' if act else 'Нет'}}
<b>Согласование</b>: {{agreement or ''}}
        """),
        Button(
            Const("Мультимедиа"),
            id="to_multimedia",
            on_click=handlers.show_operator_media,
            when="media_id",
        ),
        Button(
            Const("Сохранить"),
            id="confirm_creating",
            on_click=handlers.on_confirm,
        ),
        SwitchTo(
            Const("Изменить объект"),
            id="to_entity",
            state=states.NewSG.entity_choice,
        ),
        SwitchTo(
            Const("Изменить телефон"),
            id="to_phone",
            state=states.NewSG.phone,
        ),
        SwitchTo(
            Const("Изменить Тему"),
            id="to_title",
            state=states.NewSG.title,
        ),
        SwitchTo(
            Const("Изменить расчетное время"),
            id="to_recom_time",
            state=states.NewSG.recom_time,
        ),
        SwitchTo(
            Const("Изменить приоритет"),
            id="to_priority",
            state=states.NewSG.priority,
        ),
        SwitchTo(
            Const("Необходимость акта"),
            id="to_act",
            state=states.NewSG.act,
        ),
        SwitchTo(
            Const("Изменить описание"),
            id="to_description",
            state=states.NewSG.description,
        ),
        SwitchTo(
            Const("Изменить исполнителя"),
            id="to_slave",
            state=states.NewSG.performer,
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
    user = employee_service.get_one(userid=dialog_manager.event.from_user.id)
    return user and user.get("position") == "operator"


def user_is_performer(data, widget, dialog_manager: DialogManager) -> bool:
    return dialog_manager.event.from_user.id == data.get("slave")


def isnt_arriving(data, widget, dialog_manager: DialogManager) -> bool:
    record = journal_service.get_by_filters(
        date=datetime.today().date(),
        object=data["name"],
        taskid=data["taskid"],
        record="%Приехал%",
    )
    return bool(not record and data["status"] == config.TasksStatuses.AT_WORK)


def media_exist(data, widget, dialog_manager: DialogManager):
    return all([data.get("media_id"), data.get("is_employee")])


def act_exist(data, widget, dialog_manager: DialogManager):
    return all([data.get("actid"), data.get("is_employee")])


def videoreport_exist(data, widget, dialog_manager: DialogManager):
    return all([data.get("resultid"), data.get("is_employee")])


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
        Format("Телефон: {phone}", when="phone"),
        Format("Объект: {name}", when="name"),
        Format("Тема: {title}"),
        Format("Описание: {description}", when="description"),
        Format("Расчетное время: {recom_time}ч.", when="recom_time"),
        Format("Исполнитель: {username}", when="username"),
        Jinja('{{"помощник" if simple_report else ""}}'),
        Const("<b>Высокий приоритет!</b>", when="priority"),
        Format("Статус: {status}"),
        Format("\nНужен акт", when="act"),
        Format("<b><i><u>Согласование: {agreement}</u></i></b>", when="agreement"),
        Url(Const("Геолокация(яндекс)"), Format("{address}"), when=F["address"]),
        Button(
            Const("Видео, фото..."),
            id="mm_description",
            on_click=handlers.show_operator_media,
            when=media_exist,
        ),
        Button(
            Const("Видео от исполнителя"),
            id="to_media",
            on_click=handlers.show_performer_media,
            when=videoreport_exist,
        ),
        Button(
            Const("Акт"),
            id="act",
            on_click=handlers.show_act,
            when=act_exist,
        ),
        Group(
            Button(
                Const("Редактировать"),
                id="edit_task",
                on_click=handlers.edit_task,
                when=F["status"].not_in([
                    config.TasksStatuses.ARCHIVE,
                    config.TasksStatuses.CHECKED,
                    config.TasksStatuses.PERFORMED,
                ]),
            ),
            Button(
                Const("Отложить"),
                id="delay_task",
                on_click=handlers.on_delay,
                when=F["status"].not_in([
                    config.TasksStatuses.DELAYED,
                    config.TasksStatuses.CHECKED,
                    config.TasksStatuses.ARCHIVE,
                    config.TasksStatuses.PERFORMED,
                ]),
            ),
            Button(
                Const("Переместить в архив"),
                id="close_task",
                on_click=handlers.on_close,
                when=F["status"] != config.TasksStatuses.ARCHIVE,
            ),
            Button(
                Const("Вернуть в работу"),
                id="return_to_work",
                on_click=handlers.on_return,
                when=F["status"].in_([
                    config.TasksStatuses.PERFORMED,
                    config.TasksStatuses.ARCHIVE,
                    config.TasksStatuses.CHECKED,
                ]),
            ),
            SwitchTo(
                Const("Дополнить описание/медиа"),
                id="add_media",
                state=states.TasksSG.add_media,
                when=F["status"].in_([
                    config.TasksStatuses.PERFORMED,
                    config.TasksStatuses.ARCHIVE,
                    config.TasksStatuses.CHECKED,
                ]),
            ),
            Button(
                Const("Клонировать заявку"), id="clone_task", on_click=handlers.on_clone
            ),
            Button(Const("Удалить заявку"), id="rm_task", on_click=handlers.on_remove),
            when=user_is_operator,
        ),
        Group(
            Button(
                Const("Принять"),
                id="accept_task",
                on_click=handlers.accept_task,
                when=F["status"] == config.TasksStatuses.ASSIGNED,
            ),
            Button(
                Const("Приехал на объект"),
                id="arrived_to_object",
                on_click=handlers.on_arrived,
                when=isnt_arriving,
            ),
            Button(
                Const("Выполнено"),
                id="perform_task",
                on_click=handlers.on_perform,
                when=F["status"].not_in([
                    config.TasksStatuses.PERFORMED,
                    config.TasksStatuses.ARCHIVE,
                    config.TasksStatuses.CHECKED,
                    config.TasksStatuses.ASSIGNED,
                ]),
            ),
            Button(
                Const("Переделать"),
                id="back_to_work",
                on_click=handlers.get_back,
                when=F["status"] == config.TasksStatuses.PERFORMED,
            ),
            when=user_is_performer,
        ),
        Next(Const("Журнал заявки"), on_click=handlers.reset_journal_page),
        Button(Const("Обновить"), id="reload"),
        Back(Const("Назад")),
        state=states.TasksSG.task,
        getter=getters.task,
    ),
    Window(
        Const("<b>Журнал заявки\n\n</b>"),
        List(Format("{item[dttm]}\n{item[record]}\n"), items="journal"),
        StubScroll(id="scroll_taskjournal", pages="pages"),
        Group(NumberedPager(scroll="scroll_taskjournal", when=F["pages"] > 1), width=7),
        Back(Const("Назад")),
        state=states.TasksSG.journal,
        getter=getters.journal_getter,
    ),
    Window(
        Const("Дополнить описание/медиа"),
        MessageInput(func=handlers.add_description),
        SwitchTo(Const("Назад"), id="to_task", state=states.TasksSG.task),
        state=states.TasksSG.add_media,
    ),
    Window(
        Format(
            "В журнал будет добавлена запись о том, что вы прибыли на объект {dialog_data[task][name]}"
        ),
        Button(
            Const("Подтвердить"),
            id="confirm_arrived",
            on_click=handlers.confirm_arrived,
        ),
        SwitchTo(Const("Назад"), id="back_to_task", state=states.TasksSG.task),
        state=states.TasksSG.confirm_arrived,
    ),
)


media = Dialog(
    Window(
        Format("{wintitle}"),
        DynamicMedia("media"),
        StubScroll(id="media_scroll", pages="pages"),
        Group(NumberedPager(scroll="media_scroll", when=F["pages"] > 1), width=8),
        Cancel(Const("Назад")),
        state=states.MediaSG.main,
        getter=getters.media,
    )
)


async def on_fltr_start(data, manager: DialogManager):
    manager.dialog_data["wintitle"] = config.TasksTitles.SEARCH_RESULT


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
