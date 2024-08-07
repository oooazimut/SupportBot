from aiogram.fsm.state import State, StatesGroup


class NewSG(StatesGroup):
    entity_choice = State()
    entities = State()
    phone = State()
    title = State()
    description = State()
    priority = State()
    act = State()
    performer = State()
    agreement = State()
    preview = State()


class TasksSG(StatesGroup):
    tasks = State()
    task = State()


class MediaSG(StatesGroup):
    main = State()
