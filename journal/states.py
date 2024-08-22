from aiogram.fsm.state import State, StatesGroup


class JrMainMenuSG(StatesGroup):
    main = State()
    location = State()
    confirm = State()

class JrSearchSG(StatesGroup):
    datestamp = State()
    result = State()
    
