from aiogram import F
from aiogram.enums import ContentType
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    Column,
    Group,
    Next,
    NumberedPager,
    Row,
    Select,
    Start,
    StubScroll,
    WebApp,
)
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format, Multi
from apscheduler.executors.base import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
from db.service import task_service
from tasks import states as tsk_states
from journal import states as jrn_states

from . import handlers, states, getters

logger = logging.getLogger(__name__)


async def on_start(any, manager: DialogManager):
    scheduler: AsyncIOScheduler = manager.middleware_data.get("scheduler")
    scheduler.print_jobs()


main = Dialog(
    Window(
        Const("Главное меню:"),
        Start(Const("Заявки"), id="tasks", state=states.OpTasksSG.main),
        Start(Const("Журнал"), id="to_journal", state=jrn_states.JrMainMenuSG.main),
        WebApp(Const("Админка"), Const("https://azimut-asutp.ru/admin")),
        state=states.OpMainMenuSG.main,
    ),
    on_start=on_start,
)


def acts_are_existing(data, widget, dialog_manager: DialogManager) -> bool:
    userid = dialog_manager.event.from_user.id
    return (
        bool(task_service.get_by_filters(status=config.TasksStatuses.CHECKED))
        and userid == config.CHIEF_ID
    )


tasks = Dialog(
    Window(
        Const("Заявки:"),
        Start(
            Const("Создать"),
            id="new_task",
            data={},
            state=tsk_states.NewSG.entity_choice,
        ),
        Group(
            Start(
                Multi(
                    Const("\U0000203c", when="tasks_exists"),
                    Const(config.TasksTitles.FROM_CUSTOMER),
                    sep=" ",
                ),
                id="to_from_customers",
                state=tsk_states.TasksSG.tasks,
                data={"wintitle": config.TasksTitles.FROM_CUSTOMER},
            ),
            Start(
                Const(config.TasksTitles.OPENED),
                id="to_opened_tasks",
                state=tsk_states.TasksSG.tasks,
                data={"wintitle": config.TasksTitles.OPENED},
            ),
            Start(
                Const(config.TasksTitles.ARCHIVE),
                id="to_archive",
                state=tsk_states.TasksSG.tasks,
                data={"wintitle": config.TasksTitles.ARCHIVE},
            ),
            Start(
                Const("Поиск"),
                id="to_filtration",
                state=tsk_states.FiltrationSG.subentity,
            ),
            Start(
                Const("Проверить акты"),
                id="to_acts_checking",
                state=tsk_states.TasksSG.tasks,
                data={"wintitle": config.TasksTitles.CHECKED},
                when=acts_are_existing,
            ),
            Button(Const("Обновить"), id="reload"),
            Cancel(Const("Назад")),
            width=2,
        ),
        state=states.OpTasksSG.main,
        getter=getters.client_tasks_exists_getter,
    ),
)

close_task = Dialog(
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
        state=states.OpCloseTaskSG.closing_choice,
        getter=getters.closing_types_geter,
    ),
    Window(
        Const("В архив или добавляем информацию?"),
        Next(Const("Добавить заметку или медиа")),
        Button(
            Const("Отправить в архив"), id="confirm_closing", on_click=handlers.on_close
        ),
        Cancel(Const("Отмена")),
        state=states.OpCloseTaskSG.confirm_closing,
    ),
    Window(
        Const("Здесь можно добавить информацию по закрытию заявки в любом формате:"),
        Format("{task[description]}"),
        DynamicMedia("media", when=F["task"]["media_id"]),
        StubScroll(id="summary_media_scroll", pages="pages"),
        Group(
            NumberedPager(scroll="summary_media_scroll", when=F["pages"] > 1),
            width=8,
        ),
        MessageInput(
            func=handlers.summary_handler,
            content_types=[
                ContentType.TEXT,
                ContentType.AUDIO,
                ContentType.VIDEO,
                ContentType.DOCUMENT,
                ContentType.PHOTO,
            ],
        ),
        Back(Const("Назад к закрытию")),
        Cancel(Const("Отмена закрытия")),
        state=states.OpCloseTaskSG.summary,
        getter=getters.description_getter,
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
