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
    Start,
)
from aiogram_dialog.widgets.text import Const
from journal import states as jrn_states
from tasks import states as tsk_states

from . import handlers, states

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
            Back(Const("Назад")),
        ),
        state=states.PrfMainMenuSG.tasks,
    ),
)


performed = Dialog(
    Window(
        Const("Добавление акта."),
        MessageInput(func=handlers.act_handler, content_types=[ContentType.PHOTO]),
        Cancel(Const("Отмена")),
        state=states.PrfPerformedSG.pin_act,
    ),
    Window(
        Const("Что дальше?"),
        Next(Const("К добавлению видео")),
        Back(Const("Добавить еще один акт")),
        Cancel(Const("Отмена")),
        state=states.PrfPerformedSG.act_or_video,
    ),
    Window(
        Const("Добавление видеоотчёта:"),
        MessageInput(func=handlers.pin_videoreport, content_types=[ContentType.VIDEO]),
        Cancel(Const("Отмена")),
        state=states.PrfPerformedSG.pin_videoreport,
    ),
    Window(
        Const("Подтверждение выполнения"),
        Back(Const("Добавить еще одно видео")),
        Next(Const("Добавить текстовую заметку")),
        Cancel(
            Const("Подтвердить выполнение"),
            id="confirm_performing",
            on_click=handlers.on_close,
        ),
        Cancel(Const("Отмена")),
        state=states.PrfPerformedSG.confirm,
    ),
    Window(
        Const("Введите текст"),
        MessageInput(func=handlers.pin_text, content_types=ContentType.TEXT),
        Back(Const("Назад")),
        Cancel(Const("Отмена")),
        state=states.PrfPerformedSG.note,
    ),
)
