from aiogram.fsm.state import State, StatesGroup


class OpMainMenuSG(StatesGroup):
    main = State()

class OpTasksSG(StatesGroup):
    main = State()


class OpDelayingSG(StatesGroup):
    main = State()

class OpCloseTaskSG(StatesGroup):
    summary = State()
