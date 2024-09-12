import asyncio
import csv
from collections import defaultdict
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters.callback_data import CallbackData
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import CHIEF_ID
from custom.bot import MyBot
from db.service import JournalService, TaskService


async def reminders_task_to_worker():
    tasks = TaskService.get_task_reminder()
    bot: Bot = MyBot.get_instance()
    for task in tasks:
        try:
            messaga = await bot.send_message(
                chat_id=task["slave"], text="Есть заявки с высоким приоритетом!"
            )
            await asyncio.sleep(30)
            await messaga.delete()
        except (TelegramBadRequest, TelegramForbiddenError):
            pass


async def reminders_task_to_morning():
    tasks = TaskService.get_task_reminder_for_morning()
    bot: Bot = MyBot.get_instance()
    for task in tasks:
        messaga = await bot.send_message(
            chat_id=task["slave"], text="У вас еще остались незавершенные дела"
        )
        await asyncio.sleep(60)
        await messaga.delete()


async def close_task(taskid: int):
    TaskService.change_status(taskid, "закрыто")


class TaskFactory(CallbackData, prefix="taskfctr"):
    action: str
    task: str


async def new_task(slaveid: int, task: str, taskid: int):
    bot: Bot = MyBot.get_instance()
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="Хорошо", callback_data=TaskFactory(action="get", task=str(taskid))
    )
    try:
        messaga = await bot.send_message(
            chat_id=slaveid,
            text=f"Новая заявка: {task}",
            reply_markup=keyboard.as_markup(),
        )
        await asyncio.sleep(295)
        await messaga.delete()
    except (TelegramBadRequest, TelegramForbiddenError):
        pass


async def confirmed_task(operatorid, slave, title, taskid):
    bot: Bot = MyBot.get_instance()
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="Хорошо", callback_data=TaskFactory(action="сonfirmed", task=str(taskid))
    )
    try:
        messaga = await bot.send_message(
            chat_id=operatorid,
            text=f"{slave} выполнил заявку {title}.",
            reply_markup=keyboard.as_markup(),
        )
        await asyncio.sleep(295)
        await messaga.delete()
    except (TelegramBadRequest, TelegramForbiddenError):
        pass


async def closed_task(slaveid, task, taskid):
    bot: Bot = MyBot.get_instance()
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="Хорошо", callback_data=TaskFactory(action="closed", task=str(taskid))
    )
    try:
        messaga = await bot.send_message(
            chat_id=slaveid,
            text=f"Заявка {task} закрыта и перемещена в архив.",
            reply_markup=keyboard.as_markup(),
        )
        await asyncio.sleep(295)
        await messaga.delete()
    except (TelegramBadRequest, TelegramForbiddenError):
        pass


async def returned_task(slaveid, task, taskid):
    bot: Bot = MyBot.get_instance()
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="Хорошо", callback_data=TaskFactory(action="returned", task=str(taskid))
    )
    try:
        messaga = await bot.send_message(
            chat_id=slaveid,
            text=f"Заявка {task} возвращена вам в работу.",
            reply_markup=keyboard.as_markup(),
        )
        await asyncio.sleep(295)
        await messaga.delete()
    except (TelegramBadRequest, TelegramForbiddenError):
        pass


async def two_reports():
    def process_records(data):
        """Функция обработки записей."""
        keys = ["username", "record", "dttm", "name"]
        roadwords = ["приехал", "уехал"]
        taskwords = ["выполнено"]

        # Преобразуем дату и фильтруем данные по ключевым словам
        processed_data = [
            {
                key: datetime.strptime(record[key], "%Y-%m-%d %H:%M:%S")
                if key == "dttm"
                else record[key]
                for key in keys
                if key in record
            }
            for record in data
        ]

        road = [
            rec
            for rec in processed_data
            if any(word in rec["record"].lower() for word in roadwords)
        ]
        tasks = [
            rec
            for rec in processed_data
            if any(word in rec["record"].lower() for word in taskwords)
        ]

        grouped_road = defaultdict(list)
        for entry in sorted(road, key=lambda x: x["username"].split()[-1]):
            grouped_road[entry["username"]].append(entry)
        return grouped_road, tasks

    def write_summary(writer, report, total_road, total_obj, total_office):
        """Вывод общей информации по времени."""
        if any(len(lst) > 1 for lst in (total_road, total_obj, total_office)):
            print("  Общее время:", file=report)

        for name, times in (
            ("Офис", total_office),
            ("Объекты", total_obj),
            ("Дорога", total_road),
        ):
            total_time = sum(times, timedelta())
            if len(times) > 1:
                print(f"    {name}: {total_time}", file=report)
            writer.writerow([name, total_time])

    def generate_report(road, tasks):
        """Генерация текстового и CSV отчета."""
        with open("отчет.txt", "w") as report, open(
            "отчет.csv", "w", encoding="cp1251", newline=""
        ) as csv_report:
            writer = csv.writer(csv_report, delimiter=";")

            for user, entries in road.items():
                total_road, total_obj, total_office = [], [], []
                print(user, file=report)
                writer.writerow([user, ""])

                for i in range(1, len(entries)):
                    prev, curr = entries[i - 1], entries[i]
                    time_spent = curr["dttm"] - prev["dttm"]

                    print(
                        f"  {prev['dttm'].time()} {prev['record']} {curr['dttm'].time()} {curr['record']}",
                        file=report,
                    )

                    if "уехал" in prev["record"].lower():
                        print(
                            f"    время дороги до {curr['record'].split()[0]}: {time_spent}",
                            file=report,
                        )
                        total_road.append(time_spent)
                    else:
                        if "объект" in curr["record"].lower():
                            obj_name = next(
                                (
                                    task["name"]
                                    for task in tasks
                                    if prev["dttm"] < task["dttm"] < curr["dttm"]
                                    and curr["username"] == task["username"]
                                ),
                                "объект не определён",
                            )
                            print(
                                f"    объект: {obj_name}, время: {time_spent}",
                                file=report,
                            )
                            total_obj.append(time_spent)
                        else:
                            print(f"    Офис, время: {time_spent}", file=report)
                            total_office.append(time_spent)

                    print(file=report)

                # Запись итоговой информации
                write_summary(writer, report, total_road, total_obj, total_office)
                print(file=report)
                writer.writerow([])

    # Получение данных и вызов основных функций
    data = JournalService.get_records(
        data={"date": datetime.now().date() - timedelta(days=1)}
    )
    road, tasks = process_records(data)
    generate_report(road, tasks)


async def send_report():
    bot: Bot = MyBot.get_instance()
    await bot.send_document(1740579878, document=FSInputFile("отчет.csv"))
    await bot.send_document(CHIEF_ID, document=FSInputFile("отчет.txt"))
