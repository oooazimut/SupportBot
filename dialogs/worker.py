from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import SwitchTo, Back
from aiogram_dialog.widgets.text import Const

from handlers.worker_handlers import assigned_handler, in_progress_handler, archive_handler
from states import WorkerSG

main_dialog = Dialog(
    Window(
        Const('Ваши заявки:'),
        SwitchTo(Const('Назначенные'), id='worker_assigned', state=WorkerSG.task_list, on_click=assigned_handler),
        SwitchTo(Const('В работе'), id='worker_in_progress', state=WorkerSG.task_list, on_click=in_progress_handler),
        SwitchTo(Const('Архив'), id='worker_archive', state=WorkerSG.task_list, on_click=archive_handler),
        state=WorkerSG.main
    ),
    Window(
        Const('Заявки: '),
        Back(Const('Назад')),
        state=WorkerSG.task_list
    )
)
