from datetime import datetime
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button

from config import TasksStatuses
from db.service import employee_service, journal_service, task_service
from notifications import new_task_notification


async def on_confirm(clb: CallbackQuery, button: Button, manager: DialogManager):
    def prepare_data(data: dict, operator_id: int, current_dttm: datetime) -> dict:
        """Готовит данные для задачи, добавляя недостающие поля."""
        task_keys = task_service.get_keys()
        data = {key: value for key, value in data.items() if key in task_keys}
        defaults = {
            "status": "открыто",
            "created": current_dttm,
            "creator": operator_id,
            "entity": None,
            "agreement": None,
            "priority": None,
            "phone": None,
            "title": None,
            "description": None,
            "media_id": None,
            "media_type": None,
            "slave": None,
            "simple_report": None,
            "slaves": [],
        }
        for key, value in defaults.items():
            data.setdefault(key, value)
        return data

    async def process_task(data: dict) -> dict:
        """Обрабатывает задачу: создает или обновляет."""
        if data.get("slaves"):
            first = data["slaves"].pop(0)
            data["slave"], role = first
            data["simple_report"] = 1 if role == "пом" else None

        if data.get("taskid"):
            task = task_service.update(**data)
        else:
            task = task_service.new(**data)

        await new_task_notification([task["slave"]], task["title"], task["taskid"])
        return task

    async def log_task_action(task_id: int, message: str, current_dttm):
        """Записывает действие в журнал."""
        recdata = {
            "dttm": current_dttm,
            "task": task_id,
            "record": message,
        }
        journal_service.new(**recdata)

    current_dttm = datetime.now().replace(microsecond=0)
    operator = employee_service.get_one(clb.from_user.id)
    data = manager.dialog_data.get("task", {})
    data = prepare_data(data, clb.from_user.id, current_dttm)

    # Установка статуса
    data["status"] = (
        TasksStatuses.ASSIGNED
        if data.get("slaves") or data.get("slave")
        else TasksStatuses.OPENED
    )

    if data.get("taskid"):
        task = await process_task(data)
        await log_task_action(
            task["taskid"], f"Заявку отредактировал {operator['username']}"
        )

        # Обработка возврата
        if data.get("return"):
            del data["return"]
            await log_task_action(
                task["taskid"], f"Заявку вернул в работу {operator['username']}"
            )

        await clb.answer("Заявка отредактирована.", show_alert=True)
    else:
        task = await process_task(data)
        await clb.answer("Заявка создана.", show_alert=True)

        # Уведомление операторов
        user_ids = [
            user["userid"]
            for user in employee_service.get_by_filters(position="operator")
        ]
        await new_task_notification(
            user_ids, task.get("title", ""), task.get("taskid", "")
        )

    await manager.done(show_mode=ShowMode.DELETE_AND_SEND)
