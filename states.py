from aiogram.filters.state import StatesGroup, State


class OperatorSG(StatesGroup):
    main = State()


class CustomerSG(StatesGroup):
    main = State()
    active_tasks = State()
    task = State()


class TaskCreating(StatesGroup):
    enter_entity = State()
    enter_phone = State()
    enter_title = State()
    enter_description = State()


class WorkerSG(StatesGroup):
    main = State()
    assigned = State()
    in_progress = State()
    archive = State()

class WorkerTaskSG(StatesGroup):
    main = State()

class CustomerTaskSG(StatesGroup):
    main = State()