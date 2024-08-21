from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Column, Next, Select
from aiogram_dialog.widgets.text import Const, Format, List

from custom.babel_calendar import CustomCalendar
from tasks.handlers import on_date, on_performer

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
        Const("Выбор сотрудника"),
        Column(
            Select(
                Format("{item[username]}"),
                id="performers_choice",
                item_id_getter=lambda x: x.get("userid"),
                items="users",
                on_click=on_performer,
            )
        ),
        Next(Const('Пропустить')),
        Cancel(Const('Отмена')),
        state=states.JrSearchSG.user,
        getter=getters.users,
    ),
    Window(
        Const("Выбор даты"),
        CustomCalendar(id="cal", on_click=on_date),
        Next(Const('Пропустить')),
        Back(Const("Назад"), when=~F['start_data']),
        Cancel(Const('Отмена')),
        state=states.JrSearchSG.datestamp,
    ),
    Window(
        Const("<b>Результат\n\n</b>"),
        List(Format('{item[dttm]}\n{item[record]}\n'), items="journal"),
        Next(Const('Пропустить')),
        Back(Const("Назад")),
        Cancel(Const('Отмена')),
        state=states.JrSearchSG.result,
        getter=getters.result,
    ),
)
