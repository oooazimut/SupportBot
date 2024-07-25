import datetime
from typing import Any

import config
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from apscheduler.schedulers.asyncio import AsyncIOScheduler, asyncio
from db import empl_service, task_service
from jobs import closed_task, returned_task

from . import states


async def on_addit(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(OpTaskSG.additional)


async def on_act(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(OpTaskSG.act, show_mode=ShowMode.DELETE_AND_SEND)


async def on_back_to_preview(callback, button, manager: DialogManager):
    await manager.switch_to(OpTaskSG.preview, show_mode=ShowMode.SEND)


# Хендлеры для сотрудников
async def go_operator(
    callback_query: CallbackQuery, button: Button, manager: DialogManager
):
    operators = empl_service.get_employees_by_position("operator")
    if operators:
        manager.dialog_data["operators"] = operators
        await manager.switch_to(WorkersSG.opr)
    else:
        await callback_query.answer("Операторы отсутствуют.", show_alert=True)


async def go_worker(
    callback_query: CallbackQuery, button: Button, manager: DialogManager
):
    workers = empl_service.get_employees_by_position("worker")
    if workers:
        manager.dialog_data["workers"] = workers
        await manager.switch_to(WorkersSG.slv)
    else:
        await callback_query.answer("Работники отсутствуют.", show_alert=True)


async def go_addslaves(
    callback_query: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(WorkersSG.add_slv)


async def to_all_tasks(clb, btn, manager: DialogManager):
    await manager.switch_to(OpTaskSG.tas)


async def insert_slaves(
    callback_query: CallbackQuery, button: Button, manager: DialogManager
):
    name = manager.find("user_name").get_value()
    user_id = manager.find("user_id").get_value()
    empl_service.save_employee(user_id, name, "worker")
    await callback_query.answer("Новый работник добавлен.", show_alert=True)
    await manager.done()


async def insert_operator(
    callback_query: CallbackQuery, button: Button, manager: DialogManager
):
    name = manager.find("user_name").get_value()
    user_id = manager.find("user_id").get_value()
    empl_service.save_employee(user_id, name, "operator")
    await callback_query.answer("Новый оператор добавлен.", show_alert=True)
    await manager.done()


async def operator_getter(dialog_manager: DialogManager, **kwargs):
    un = dialog_manager.dialog_data["operators"]
    return {"un": un}


async def worker_getter(dialog_manager: DialogManager, **kwargs):
    try:
        un = dialog_manager.dialog_data["workers"]
    except KeyError:
        un = dialog_manager.start_data["workers"]
    return {"un": un}


async def edit_task(callback: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(TaskCreating.preview, data=manager.dialog_data["task"])


async def on_type(
    callback: CallbackQuery, select, dialog_manager: DialogManager, c_type: str, /
):
    dialog_manager.dialog_data["c_type"] = c_type
    await dialog_manager.next()


async def on_close(message: Message, widget: Any, manager: DialogManager):
    taskid = manager.dialog_data["task"]["taskid"]
    operator = config.AGREEMENTERS.get(message.from_user.id)
    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
    summary = manager.dialog_data.get("task", {}).get("summary") or ""
    add_summ = manager.find("summary").get_value() or ""
    summary += add_summ + f"\nзакрыл {operator}.\n"
    task_service.update_summary(taskid, summary)

    if manager.dialog_data.get("c_type") == "0":
        task_service.reopen(taskid)

    if (
        manager.dialog_data["task"]["status"] == "проверка"
        or not manager.dialog_data["task"]["act"]
    ):
        task_service.change_status(taskid, "закрыто")
        job = scheduler.get_job(job_id=str(taskid))
        if job:
            job.remove()
        messaga = await message.answer("Заявка перемещена в архив.")
        await asyncio.sleep(3)
        await messaga.delete()
        slave = manager.dialog_data["task"]["slave"]
        task = manager.dialog_data["task"]["title"]
        taskid = manager.dialog_data["task"]["taskid"]
        if slave:
            scheduler.add_job(
                closed_task,
                "interval",
                minutes=5,
                next_run_time=datetime.datetime.now(),
                args=[slave, task, taskid],
                id=str(slave) + str(taskid),
                replace_existing=True,
            )
    else:
        task_service.change_status(taskid, "проверка")
        messaga = await message.answer(
            "Заявка ушла на проверку правильного заполнения акта."
        )
        await asyncio.sleep(3)
        await messaga.delete()

    await manager.done()


async def on_return(clb: CallbackQuery, button, manager: DialogManager):
    task = manager.dialog_data["task"]
    task_service.change_status(task["taskid"], "в работе")

    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
    job = scheduler.get_job(str(task["taskid"]))
    if job:
        job.remove()
        await clb.answer("Заявка возвращена в работу.", show_alert=True)
        slave = manager.dialog_data["task"]["slave"]
        task = manager.dialog_data["task"]["title"]
        taskid = manager.dialog_data["task"]["taskid"]
        scheduler.add_job(
            returned_task,
            "interval",
            minutes=5,
            next_run_time=datetime.datetime.now(),
            args=[slave, task, taskid],
            id=str(slave) + task,
            replace_existing=True,
        )
    else:
        await clb.answer("Заявка уже в работе.", show_alert=True)

    await manager.switch_to(OpTaskSG.opened_tasks)


async def delay_handler(
    message: Message, message_input: MessageInput, manager: DialogManager
):
    delay = int(message.text)
    taskid = manager.start_data["taskid"]
    delayed_status = manager.start_data["status"]
    scheduler: AsyncIOScheduler = manager.middleware_data["scheduler"]
    trigger_data = datetime.date.today() + datetime.timedelta(days=delay)
    year, month, day = trigger_data.year, trigger_data.month, trigger_data.day

    task_service.change_status(taskid, status="отложено")
    scheduler.add_job(
        task_service.change_status,
        trigger="date",
        run_date=datetime.datetime(year, month, day, 9, 0, 0),
        args=[taskid, delayed_status],
        id="delay" + str(taskid),
    )
    await manager.done()
    messaga = await message.answer(f"Ваша заявка отложена до {trigger_data}")
    await asyncio.sleep(5)
    await messaga.delete()
