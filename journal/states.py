from aiogram.fsm.state import State, StatesGroup


class JrMainMenuSG(StatesGroup):
    main = State()
    location = State()
    confirm = State()

class JrSearchSG(StatesGroup):
    user = State()
    datestamp = State()
    result = State()
    
