from aiogram.filters.state import StatesGroup, State


class OperatorSG(StatesGroup):
    main = State()


class OpTaskSG(StatesGroup):
    tas = State()
    new_task = State()
    progress_task = State()
    archive_task = State()


class TaskSG(StatesGroup):
    main = State()


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


class WorkerSG(StatesGroup):
    tasks_entities = State()
    enter_object = State()
    enter_dialog = State()
    main = State()
    assigned = State()
    in_progress = State()
    archive = State()
    entites_on_task = State()


class WorkerSendSG(StatesGroup):
    set_worker = State()


class WorkerTaskSG(StatesGroup):
    main = State()


class CustomerTaskSG(StatesGroup):
    main = State()
