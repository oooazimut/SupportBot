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
    new_task = State()
    progress_task = State()
    archive_task = State()
    set_worker = State()


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
    enter_entity = State()
    enter_phone = State()
    enter_title = State()
    enter_description = State()
    preview = State()

class WorkerSG(StatesGroup):
    main = State()
    assigned = State()
    in_progress = State()
    archive = State()


class WorkerTaskSG(StatesGroup):
    main = State()

class CustomerTaskSG(StatesGroup):
    main = State()
