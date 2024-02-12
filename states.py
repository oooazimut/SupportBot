from aiogram.filters.state import StatesGroup, State


class OperatorSG(StatesGroup):
    main = State()


class CustomerSG(StatesGroup):
    main = State()


class TaskCreating(StatesGroup):
    enter_entity = State()
    enter_phone = State()
    enter_title = State()
    enter_description = State()


class WorkerSG(StatesGroup):
    main = State()
    task_list = State()
