from aiogram import F
from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
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
    SwitchTo,
)
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, List, Multi

from custom.babel_calendar import CustomCalendar
from tasks.handlers import on_date

from . import getters, handlers, states

main = Dialog(
    Window(
        Const("Журнал"),
        List(
            Multi(
                Format("{item[name]}", when=F["item"]["name"]),
                Format("{item[title]}", when=F["item"]["title"]),
                Format("{item[dttm]}\n{item[record]}\n"),
            ),
            items="journal",
            when="journal",
        ),
        Next(Const("Сделать запись")),
        Button(Const("Поиск"), id="to_search", on_click=handlers.on_search),
        SwitchTo(
            Const("Прикрепить чек"),
            id="to_receipt",
            state=states.JrMainMenuSG.pin_receipt,
        ),
        Cancel(Const("Отмена")),
        state=states.JrMainMenuSG.main,
        getter=getters.main_getter,
    ),
    Window(
        Const("Выберите объект"),
        Column(
            Select(
                Format("{item[name]}"),
                id="sel_location",
                item_id_getter=lambda x: x["ent_id"],
                items="locations",
                on_click=handlers.on_location,
            )
        ),
        Next(Const("Объекта нет в списке")),
        Back(Const("Назад")),
        Cancel(Const("Отмена")),
        state=states.JrMainMenuSG.location,
        getter=getters.locations_getter,
    ),
    Window(
        Const("Введите название объекта"),
        MessageInput(func=handlers.object_input, content_types=ContentType.TEXT),
        state=states.JrMainMenuSG.object_input,
    ),
    Window(
        Format("{dialog_data[location]}"),
        Column(
            Select(
                Format("{item}"),
                id="sel_action",
                item_id_getter=str,
                items="actions",
                on_click=handlers.on_action,
            )
        ),
        SwitchTo(Const("Назад"), id="to_location", state=states.JrMainMenuSG.location),
        Cancel(Const("Отмена")),
        state=states.JrMainMenuSG.action,
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
    Window(
        Const("Прикрепление чека"),
        MessageInput(handlers.pin_receipt, content_types=ContentType.PHOTO),
        Cancel(Const("Отмена")),
        state=states.JrMainMenuSG.pin_receipt,
    ),
    Window(
        Const("Выбор автомобиля"),
        Column(
            Select(
                Format("{item[model]}, {item[state_number]}"),
                id="sel_car",
                item_id_getter=lambda x: x["id"],
                items="cars",
                on_click=handlers.on_car,
            )
        ),
        state=states.JrMainMenuSG.sel_car,
        getter=getters.cars,
    ),
)

search = Dialog(
    Window(
        Const("Выбор даты"),
        CustomCalendar(id="cal", on_click=on_date),
        Next(Const("Пропустить")),
        Cancel(Const("Отмена")),
        state=states.JrSearchSG.datestamp,
    ),
    Window(
        Const("Журнал"),
        Format("<b>{username}</b>\n\n", when="username"),
        List(
            Multi(
                Format("{item[name]}", when=F["item"]["name"]),
                Format("{item[title]}", when=F["item"]["title"]),
                Format("{item[dttm]}\n{item[record]}\n"),
            ),
            items="journal",
            when="journal",
        ),
        Const("\nАвтомобили:", when='cars'),
        List(
            Format("{item[dttm]}: {item[model]} {item[state_number]}", when=F["item"]["model"]),
            items="cars",
            when="cars",
        ),
        Next(
            Const("Чеки"),
            on_click=handlers.on_checks,
            when=F["dialog_data"]["receipts"],
        ),
        StubScroll(id="users_scroll", pages="pages"),
        Group(NumberedPager(scroll="users_scroll", when=F["pages"] > 1), width=8),
        Cancel(Const("Выход")),
        state=states.JrSearchSG.result,
        getter=getters.result,
    ),
    Window(
        Format("Чеки, {username}"),
        DynamicMedia("media"),
        Format("{caption}", when="caption"),
        StubScroll(id="receipts_scroll", pages="pages"),
        Group(NumberedPager(scroll="receipts_scroll", when=F["pages"] > 1), width=8),
        Back(Const("Назад")),
        Cancel(Const("Выход")),
        state=states.JrSearchSG.receipts,
        getter=getters.receipts_getter,
    ),
)
