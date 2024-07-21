import config
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
from aiogram_dialog.widgets.text import Const, Format
from db import task_service
from getters.operators import Getters
from handlers import operators
from handlers.operators import delay_handler, on_return
from operators import handlers
from states.operators import MainMenuSG, TasksMenuSG, WorkersSG
from states.tasks import NewSG, TasksSG

main = Dialog(
    Window(
        Const("Главное меню:"),
        Row(
            Start(Const("Заявки"), id="tasks", state=TasksMenuSG.main),
            Start(Const("Работники"), id="slaves", state=WorkersSG.main),
            WebApp(Const("Админка"), Const("https://azimut-asutp.ru/admin")),
        ),
        state=MainMenuSG.main,
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
                Const("Новая заявка"), id="new_task", data={}, state=NewSG.entity_choice
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
        state=TasksMenuSG.main,
    ),
    Window(
        Jinja("""
       {{created}}
       Тема: {{title if title}}
       Объект: {{name if name}}
       Описание: {{description if description}}
       Исполнитель: {{username if username}}
       Приоритет: {{priority if priority}}
       Статус: {{status}}
       """),
        Format("Нужен акт", when=F["act"]),
        Format("<b><i><u>Согласование: {agreement}</u></i></b>", when=F["agreement"]),
        Format("\n <b>Информация по закрытию:</b> \n {summary}", when=F["summary"]),
        DynamicMedia("resultmedia", when=F["resultmedia"]),
        Button(
            Const("Доп инфо"), id="addit_info", on_click=on_addit, when=F["media_id"]
        ),
        Button(Const("Акт"), id="act", on_click=on_act, when=F["actid"]),
        Button(
            Const("Редактировать"),
            id="edit_task",
            on_click=handlers.edit_task,
            when=(F["status"] != "закрыто"),
        ),
        Button(
            Const("Отложить"),
            id="delay_task",
            on_click=operators.on_delay,
            when=(F["status"] != "отложено"),
        ),
        Button(
            Const("Переместить в архив"),
            id="close_task",
            on_click=operators.to_confirmation,
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
                on_click=handlers.on_task,
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
        state=DelayTaskSG.enter_delay,
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
