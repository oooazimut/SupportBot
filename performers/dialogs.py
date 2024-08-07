import operator

import config
from aiogram.enums import ContentType
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    Column,
    Select,
    Start,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Const, Format
from tasks import states as tsk_states

from . import getters, handlers, states

main = Dialog(
    Window(
        Const("Главное меню:"),
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
            SwitchTo(
                Const("Заявки по объектам"),
                id="tasks_for_entity",
                state=states.PrfMainMenuSG.entities_choice,
            ),
        ),
        state=states.PrfMainMenuSG.main,
    ),
    Window(
        Const(
            "Выбор объекта. Для получение объекта/объектов введите его название или хотя бы часть."
        ),
        MessageInput(handlers.entites_name_handler, content_types=[ContentType.TEXT]),
        Back(Const("Назад")),
        state=states.PrfMainMenuSG.entities_choice,
    ),
    Window(
        Const("Объекты"),
        Column(
            Select(
                Format("{item[name]}"),
                id="objects",
                item_id_getter=operator.itemgetter("ent_id"),
                items="objects",
                on_click=handlers.on_entity,
            )
        ),
        Back(Const("Назад")),
        SwitchTo(Const("Главное меню"), id="to_main", state=states.PrfMainMenuSG.main),
        state=states.PrfMainMenuSG.entities,
        getter=getters.task_entities_getter,
    ),
)


performed = Dialog(
    Window(
        Const("К этой заявке необходимо приложить фото акта."),
        MessageInput(func=handlers.act_handler, content_types=[ContentType.PHOTO]),
        Cancel(Const("Назад")),
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
