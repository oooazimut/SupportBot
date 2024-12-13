from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Start
from aiogram_dialog.widgets.text import Const

from journal import states as jr_states

from . import states

main = Dialog(
    Window(
        Const("Меню"),
        Start(Const("Журнал"), id="to_journal", state=jr_states.JrMainMenuSG.main),
        state=states.ObMainMenuSG.main,
    ),
)
