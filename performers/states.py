from aiogram.fsm.state import State, StatesGroup


class PrfMainMenuSG(StatesGroup):
    main = State()
    tasks = State()


class PrfPerformedSG(StatesGroup):
    closing_choice = State()
    pin_act = State()
    pin_videoreport = State()
