from aiogram_dialog import DialogManager, Window
from aiogram_dialog.widgets.kbd import Start
from aiogram_dialog.widgets.text import Const


async def getter(dialog_manager: DialogManager, **kwargs):
    return {
        "name": "Ivan",
        "surname": "Ivanov",
    }


the_window = Window(
    Const("SomeText"),
    Start(
        Const("Go to another dialog"),
        id="next_dialog",
        state=AnotherSG.main,
        data={"condom_name": "name"},
    ),
    state=SomeSG.main,
)
