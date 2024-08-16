from aiogram.fsm.state import State, StatesGroup


class OpMainMenuSG(StatesGroup):
    main = State()

class OpTasksSG(StatesGroup):
    main = State()


class OpDelayingSG(StatesGroup):
    main = State()

class OpCloseTaskSG(StatesGroup):
    summary = State()

class OpRemoveTaskSG(StatesGroup):
    main = State()

class OpFiltrationSG(StatesGroup):
    subentity = State()
    entities = State()
    performer = State()
    datestamp = State()
    status = State()
