from aiogram.filters.state import StatesGroup, State


class OperatorSG(StatesGroup):
    main = State()


class OpTaskSG(StatesGroup):
    tas = State()
    new_task = State()
    progress_task = State()
    archive_task = State()
    preview = State()


class WorkersSG(StatesGroup):
    main = State()
    opr = State()
    slv = State()


class CustomerSG(StatesGroup):
    main = State()
    slave = State()
    active_tasks = State()
    task = State()


class TaskCreating(StatesGroup):
    sub_entity = State()
    entities = State()
    empty_entities = State()
    enter_phone = State()
    enter_title = State()
    enter_description = State()
    priority = State()
    slave = State()
    preview = State()


class PerformedTaskSG(StatesGroup):
    main = State()


class WorkerSG(StatesGroup):
    main = State()
    assigned = State()
    in_progress = State()
    archive = State()
    entities_search = State()
    enter_object = State()
    tasks_entities = State()


class WorkerTaskSG(StatesGroup):
    main = State()
    media_pin = State()


class CustomerTaskSG(StatesGroup):
    main = State()
