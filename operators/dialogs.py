import config
from aiogram import F
from aiogram.enums import ContentType
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Cancel,
    Column,
    Row,
    Select,
    Start,
    WebApp,
)
from aiogram_dialog.widgets.text import Const, Format
from db import task_service
from operators import getters
from tasks.states import NewSG, TasksSG

from . import handlers, states

main = Dialog(
    Window(
        Const("Главное меню:"),
        Row(
            Start(Const("Заявки"), id="tasks", state=states.TasksMenuSG.main),
            Start(Const("Работники"), id="slaves", state=states.WorkersSG.main),
            WebApp(Const("Админка"), Const("https://azimut-asutp.ru/admin")),
        ),
        state=states.MainMenuSG.main,
    ),
)


def acts_are_existing(data, widget, dialog_manager: DialogManager) -> bool:
    userid = dialog_manager.event.from_user.id
    return (
        bool(task_service.get_tasks_by_status("проверка")) and userid == config.CHIEF_ID
    )


tasks = Dialog(
    Window(
        Const("Заявки:"),
        Row(
            Start(
                Const("Новая заявка"),
                id="new_task",
                data={},
                state=NewSG.entity_choice,
            ),
            Start(
                Const(str(config.TasksTitles.OPENED)),
                id="to_opened_tasks",
                state=TasksSG.tasks,
                data={"wintitle": config.TasksTitles.OPENED},
            ),
            Start(
                Const(str(config.TasksTitles.ARCHIVE)),
                id="to_archive",
                state=TasksSG.tasks,
                data={"wintitle": config.TasksTitles.ARCHIVE},
            ),
        ),
        Start(
            Const("Проверить акты"),
            id="to_acts_checking",
            state=TasksSG.tasks,
            data={"wintitle": config.TasksTitles.CHECKED},
            when=acts_are_existing,
        ),
        Cancel(Const("Назад")),
        state=states.TasksMenuSG.main,
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
        getter=getters.closingtype_getter,
        state=states.CloseTaskSG.type_choice,
    ),
    Window(
        Const("Здесь можно добавить информацию по закрытию заявки:"),
        MessageInput(func=handlers.on_close, content_types=[ContentType.TEXT, ]),
        state=states.CloseTaskSG.summary,
    ),

)

d = Dialog(
    Window(
        Button(
            Const("Редактировать"),
            id="edit_task",
            on_click=handlers.edit_task,
            when=(F["status"] != "закрыто"),
        ),
        Button(
            Const("Отложить"),
            id="delay_task",
            on_click=handlers.on_delay,
            when=(F["status"] != "отложено"),
        ),
        Button(
            Const("Переместить в архив"),
            id="close_task",
            on_click=handlers.to_confirmation,
            when=(F["status"] != "закрыто"),
        ),
        Button(
            Const("Вернуть в работу"),
            id="return_to_work",
            on_click=on_return,
            when=(F["status"] == "выполнено"),
        ),
        Button(Const("Назад"), id="to_all_tasks", on_click=to_all_tasks),
        state=OpTaskSG.preview,
        getter=Getters.review,
    ),
    Window(
        Const("Как вы хотите закрыть заявку?"),
        Button(Const("Частично"), id="partial_closing"),
        Button(Const("Полностью"), id="full_closing"),
        state=OpTaskSG.choose_closetype,
    ),
    Window(
        Const("Здесь можно добавить информацию по закрытию заявки:"),
        MessageInput(),
        TextInput(id="summary", on_success=operators.on_close),
        state=OpTaskSG.summary,
    ),
    Window(
        Const("Проверить акты:"),
        Column(
            Select(
                JINJA_TEMPLATE,
                id="tasks_with_acts",
                item_id_getter=lambda x: x["taskid"],
                items="tasks",
                on_click=operators.on_task,
            ),
        ),
        state=OpTaskSG.with_acts,
        getter=Getters.with_acts,
    ),
    Window(
        DynamicMedia("media"),
        Button(Const("Назад"), id="to_preview", on_click=on_back_to_preview),
        state=OpTaskSG.additional,
        getter=Getters.addition,
    ),
    Window(
        DynamicMedia("media"),
        Button(Const("Назад"), id="to_preview", on_click=on_back_to_preview),
        state=OpTaskSG.act,
        getter=Getters.act,
    ),
)

delay = Dialog(
    Window(
        Const("Введите количество дней, на которое вы хотите отложить заявку"),
        MessageInput(handlers.delay_handler, content_types=[ContentType.TEXT]),
        Cancel(Const("Назад")),
        state=states.DelayingSG.main,
    ),
)


# workers = Dialog(
#     Window(
#         Const("Работники:"),
#         Row(
#             Button(Const("Операторы"), id="assigned", on_click=operators.go_operator),
#             Button(
#                 Const("Исполнители"), id="worker_archive", on_click=operators.go_worker
#             ),
#             Button(
#                 Const("Добавить работника"),
#                 id="add_worker",
#                 on_click=operators.go_addslaves,
#             ),
#         ),
#         Cancel(Const("Назад")),
#         state=WorkersSG.main,
#     ),
#     Window(
#         Const("Список операторов:"),
#         Column(
#             Select(
#                 Format("{item[username]}"),
#                 id="operators",
#                 item_id_getter=operator.itemgetter("userid"),
#                 items="un",
#             )
#         ),
#         SwitchTo(Const("Назад"), id="to_main", state=WorkersSG.main),
#         state=WorkersSG.opr,
#         getter=operators.operator_getter,
#     ),
#     Window(
#         Const("Список работников:"),
#         Column(
#             Select(
#                 Format("{item[username]}"),
#                 id="workers",
#                 item_id_getter=operator.itemgetter("userid"),
#                 items="un",
#             )
#         ),
#         SwitchTo(Const("Назад"), id="to_main", state=WorkersSG.main),
#         state=WorkersSG.slv,
#         getter=operators.worker_getter,
#     ),
#     Window(
#         Const("Введите имя сотрудника"),
#         TextInput(id="user_name", on_success=next_or_end),
#         Back(Const("Назад")),
#         CANCEL_EDIT,
#         Cancel(Const("Отменить создание")),
#         state=WorkersSG.add_slv,
#     ),
#     Window(
#         Const("Введите id сотрудника"),
#         TextInput(id="user_id", on_success=next_or_end),
#         Back(Const("Назад")),
#         Cancel(Const("Отменить создание")),
#         state=WorkersSG.add_id,
#     ),
#     Window(
#         Const("Выберите статус для сотрудника"),
#         Column(
#             Button(
#                 Const("Исполнитель"),
#                 id="slaves_status",
#                 on_click=operators.insert_slaves,
#             ),
#             Button(
#                 Const("Оператор"),
#                 id="operator_status",
#                 on_click=operators.insert_operator,
#             ),
#         ),
#         Back(Const("Назад")),
#         CANCEL_EDIT,
#         state=WorkersSG.status,
#     ),
# )
