from aiogram.enums import ContentType
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Cancel,
    Column,
    Row,
    Select,
    Start,
    WebApp,
)
from aiogram_dialog.widgets.text import Const, Format

import config
from db.service import TaskService
from operators import getters
from tasks import states as tsk_states

from . import handlers, states

main = Dialog(
    Window(
        Const("Главное меню:"),
        Row(
            Start(Const("Заявки"), id="tasks", state=states.OpTasksSG.main),
            WebApp(Const("Админка"), Const("https://azimut-asutp.ru/admin")),
        ),
        state=states.OpMainMenuSG.main,
    ),
)


def acts_are_existing(data, widget, dialog_manager: DialogManager) -> bool:
    userid = dialog_manager.event.from_user.id
    return (
        bool(TaskService.get_tasks_by_status("проверка")) and userid == config.DEV_ID
    )


tasks = Dialog(
    Window(
        Const("Заявки:"),
        Row(
            Start(
                Const("Новая заявка"),
                id="new_task",
                data={},
                state=tsk_states.NewSG.entity_choice,
            ),
            Start(
                Const(str(config.TasksTitles.OPENED.value)),
                id="to_opened_tasks",
                state=tsk_states.TasksSG.tasks,
                data={"wintitle": config.TasksTitles.OPENED.value},
            ),
            Start(
                Const(str(config.TasksTitles.ARCHIVE.value)),
                id="to_archive",
                state=tsk_states.TasksSG.tasks,
                data={"wintitle": config.TasksTitles.ARCHIVE.value},
            ),
        ),
        Start(
            Const("Проверить акты"),
            id="to_acts_checking",
            state=tsk_states.TasksSG.tasks,
            data={"wintitle": config.TasksTitles.CHECKED.value},
            when=acts_are_existing,
        ),
        Cancel(Const("Назад")),
        state=states.OpTasksSG.main,
    ),
)

close_task = Dialog(
    Window(
        Const("Как вы хотите закрыть заявку?"),
        Column(
            Select(
                Format(" {item[0]}"),
                id="sel_type",
                item_id_getter=lambda item: item[1],
                items="c_types",
                on_click=handlers.on_type,
            ),
        ),
        Cancel(Const('Назад')),
        getter=getters.closingtype_getter,
        state=states.OpCloseTaskSG.type_choice,
    ),
    Window(
        Const("Здесь можно добавить информацию по закрытию заявки:"),
        MessageInput(
            func=handlers.on_close,
            content_types=[
                ContentType.TEXT,
            ],
        ),
        state=states.OpCloseTaskSG.summary,
    ),
)


delay = Dialog(
    Window(
        Const("Введите количество дней, на которое вы хотите отложить заявку"),
        MessageInput(handlers.delay_handler, content_types=[ContentType.TEXT]),
        Cancel(Const("Назад")),
        state=states.OpDelayingSG.main,
    ),
)
