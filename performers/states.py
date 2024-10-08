from aiogram.fsm.state import State, StatesGroup


class PrfMainMenuSG(StatesGroup):
    main = State()
    tasks = State()


class PrfPerformedSG(StatesGroup):
    pin_act = State()
    act_or_video = State()
    pin_videoreport = State()
    confirm = State()
    note = State()
