from aiogram.enums import ContentType
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    Row,
    Start,
    WebApp,
)
from aiogram_dialog.widgets.text import Const
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
from db.service import TaskService
from tasks import states as tsk_states

from . import handlers, states


async def on_start(any, manager: DialogManager):
    scheduler: AsyncIOScheduler = manager.middleware_data.get("scheduler")
    scheduler.print_jobs()
    for i in scheduler.get_jobs():
        if i.name in ("closed_task", "new_task", "confirmed_task"):
            i.remove()


main = Dialog(
    Window(
        Const("Главное меню:"),
        Row(
            Start(Const("Заявки"), id="tasks", state=states.OpTasksSG.main),
            WebApp(Const("Админка"), Const("https://azimut-asutp.ru/admin")),
        ),
        state=states.OpMainMenuSG.main,
    ),
    on_start=on_start,
)


def acts_are_existing(data, widget, dialog_manager: DialogManager) -> bool:
    userid = dialog_manager.event.from_user.id
    return (
        bool(TaskService.get_tasks_by_status("проверка")) and userid == config.CHIEF_ID
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
            Const("Поиск"), id="to_filtration", state=tsk_states.FiltrationSG.subentity
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
        Const("Здесь можно добавить информацию по закрытию заявки:"),
        MessageInput(
            func=handlers.on_close,
            content_types=[
                ContentType.TEXT,
            ],
        ),
        Cancel(Const("Назад")),
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

remove = Dialog(
    Window(
        Const("Вы уверены, что хотите БЕЗВОЗВРАТНО УДАЛИТЬ заявку?"),
        Button(Const("Да"), id="confirm_del", on_click=handlers.on_remove),
        Cancel(Const("Нет")),
        state=states.OpRemoveTaskSG.main,
    )
)
