from aiogram.fsm.state import State, StatesGroup


class CusMainSG(StatesGroup):
    main = State()


class NewCustomerSG(StatesGroup):
    name = State()
    phone = State()
    object = State()
    preview = State()


class NewTaskSG(StatesGroup):
    preview = State()
