from aiogram.fsm.state import State, StatesGroup


class MainMenuSG(StatesGroup):
    main = State()

class TasksMenuSG(StatesGroup):
    main = State()

class WorkersSG(StatesGroup):
    main = State()

class DelayingSG(StatesGroup):
    main = State()

class CloseTaskSG(StatesGroup):
    type_choice = State()
