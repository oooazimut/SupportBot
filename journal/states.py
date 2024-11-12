from aiogram.fsm.state import State, StatesGroup


class JrMainMenuSG(StatesGroup):
    main = State()
    location = State()
    object_input = State()
    action = State()
    confirm = State()
    pin_receipt = State()
    sel_car = State()

class JrSearchSG(StatesGroup):
    datestamp = State()
    result = State()
    receipts = State()
    
