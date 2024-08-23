import config
from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    Column,
    Next,
    Select,
    Start,
)
from aiogram_dialog.widgets.text import Const, Format
from tasks import states as tsk_states
from journal import states as jrn_states

from . import getters, handlers, states

main = Dialog(
    Window(
        Const("Главное меню:"),
        Next(Const("Заявки")),
        Start(Const("Журнал"), id="to_journal", state=jrn_states.JrMainMenuSG.main),
        state=states.PrfMainMenuSG.main,
    ),
    Window(
        Const("Заявки"),
        Column(
            Start(
                Const("Назначенные"),
                id="worker_assigned",
                state=tsk_states.TasksSG.tasks,
                data={"wintitle": config.TasksTitles.ASSIGNED.value},
            ),
            Start(
                Const("В работе"),
                id="worker_in_progress",
                state=tsk_states.TasksSG.tasks,
                data={"wintitle": config.TasksTitles.IN_PROGRESS.value},
            ),
            Button(Const("Архив"), id="worker_archive", on_click=handlers.on_archive),
            Start(
                Const("Поиск"),
                id="to_filtration",
                state=tsk_states.FiltrationSG.subentity,
            ),
            Back(Const('Назад')),
        ),
        state=states.PrfMainMenuSG.tasks,
    ),
)


performed = Dialog(
    Window(
        Const("Все ли сделано по этой заявке?"),
        Column(
            Select(
                Format("{item[0]}"),
                id="closing_types",
                item_id_getter=lambda x: x[1],
                items="closing_types",
                on_click=handlers.on_closing_type,
            )
        ),
        Cancel(Const("Отмена")),
        state=states.PrfPerformedSG.closing_choice,
        getter=getters.closing_types_geter,
    ),
    Window(
        Const("К этой заявке необходимо приложить фото акта."),
        MessageInput(func=handlers.act_handler, content_types=[ContentType.PHOTO]),
        Back(Const("Назад")),
        Cancel(Const("Главное меню")),
        state=states.PrfPerformedSG.pin_act,
    ),
    Window(
        Const("Для закрытия заявки добавьте видеоотчёт."),
        MessageInput(handlers.pin_videoreport, content_types=[ContentType.VIDEO]),
        Back(Const("Назад")),
        Cancel(Const("Главное меню")),
        state=states.PrfPerformedSG.pin_videoreport,
    ),
)

