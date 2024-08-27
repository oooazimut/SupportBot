from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    Column,
    Group,
    Next,
    NumberedPager,
    Select,
    StubScroll,
)
from aiogram_dialog.widgets.text import Const, Format, List, Multi

from custom.babel_calendar import CustomCalendar
from tasks.handlers import on_date

from . import getters, handlers, states

main = Dialog(
    Window(
        Const("Журнал"),
        Column(
            Select(
                Format("{item}"),
                id="sel_location",
                item_id_getter=lambda x: x,
                items="locations",
                on_click=handlers.on_location,
            )
        ),
        Button(Const("Поиск"), id="to_search", on_click=handlers.on_search),
        Cancel(Const("Отмена")),
        state=states.JrMainMenuSG.main,
        getter=getters.locations,
    ),
    Window(
        Format("{dialog_data[location]}"),
        Column(
            Select(
                Format("{item}"),
                id="sel_action",
                item_id_getter=lambda x: x,
                items="actions",
                on_click=handlers.on_action,
            )
        ),
        Back(Const("Назад")),
        Cancel(Const("Отмена")),
        state=states.JrMainMenuSG.location,
        getter=getters.actions,
    ),
    Window(
        Const("Ваша запись: "),
        Format("{dialog_data[record]}"),
        Button(Const("Подтвердить"), id="confirm", on_click=handlers.on_confirm),
        Back(Const("Назад")),
        Cancel(Const("Отмена")),
        state=states.JrMainMenuSG.confirm,
    ),
)

search = Dialog(
    Window(
        Const("Выбор даты"),
        CustomCalendar(id="cal", on_click=on_date),
        Next(Const("Пропустить")),
        Back(Const("Назад"), when=~F["start_data"]),
        Cancel(Const("Отмена")),
        state=states.JrSearchSG.datestamp,
    ),
    Window(
        Const("Журнал"),
        Format("<b>{username}</b>\n\n", when="username"),
        List(
            Multi(
                Format("{item[name]}", when=F['item']['name']),
                Format("{item[title]}", when=F['item']['title']),
                Format("{item[dttm]}\n{item[record]}\n"),
            ),
            items="journal",
            when="journal",
        ),
        StubScroll(id="users_scroll", pages="pages"),
        Group(NumberedPager(scroll="users_scroll"), width=8),
        Cancel(Const("Выход")),
        state=states.JrSearchSG.result,
        getter=getters.result,
    ),
)
