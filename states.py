from aiogram.filters.state import StatesGroup, State


class OperatorSG(StatesGroup):
    main = State()
    tas = State()
    worker = State()
    new_task = State()
    progress_task = State()
    archive_task = State()
    opr = State()
    slv = State()


class CustomerSG(StatesGroup):
    main = State()
    slave = State()



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

class AddWorkerSG(StatesGroup):
    workerid = State()
    name = State()
    status = State()
    preview = State()