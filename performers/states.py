from aiogram.fsm.state import State, StatesGroup


class PrfMainMenuSG(StatesGroup):
    main = State()
    entities_choice = State()
    entities = State()

class PrfPerformedSG(StatesGroup):
    pin_act = State()
    pin_videoreport = State()
