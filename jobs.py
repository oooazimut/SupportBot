import asyncio
import csv
from collections import defaultdict
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from custom.bot import MyBot
from db.service import JournalService, TaskService
from yandex import ensure_directories_exist, get_yandex_disk_path, upload_to_yandex_disk


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
        keys = ["username", "record", "dttm", "name", "recom_time", "task"]
        roadwords = ["приехал", "уехал"]

        road = [
            rec
            for rec in data
            if any(word in rec["record"].lower() for word in roadwords)
        ]

        tasks = [rec for rec in data if rec["recom_time"] and rec['username']]

        # Преобразуем дату и фильтруем данные по ключевым словам
        processed_data = [
            {
                key: datetime.strptime(record[key], "%Y-%m-%d %H:%M:%S")
                if key == "dttm"
                else record[key]
                for key in keys
                if key in record
            }
            for record in road
        ]

        grouped_road = defaultdict(list)
        for entry in sorted(processed_data, key=lambda x: x["username"].split()[-1]):
            grouped_road[entry["username"]].append(entry)
        grouped_tasks = defaultdict(list)
        for entry in sorted(tasks, key=lambda x: x['username'].split()[-1]):
            grouped_tasks[entry['username']].append(entry)

        return grouped_road, grouped_tasks


    def write_summary(writer, report, total_road, total_obj, total_office):
        """Вывод общей информации по времени."""
        if any(lst for lst in (total_road, total_obj, total_office)):
            print("  Общее время:", file=report)

        for name, times in (
            ("Офис", total_office),
            ("Объекты", total_obj),
            ("Дорога", total_road),
        ):
            total_time = sum(times, timedelta())
            if total_time:
                print(f"    {name}: {total_time}", file=report)
                writer.writerow([name, total_time])

    def generate_report(records, tasks):
        """Генерация текстового и CSV отчета."""

        curr_date = datetime.now().date() - timedelta(days=1)
        with open(f"{curr_date}.txt", "w") as report, open(
            f"{curr_date}.csv", "w", encoding="cp1251", newline=""
        ) as csv_report:
            writer = csv.writer(csv_report, delimiter=";")

            print(curr_date, file=report)
            print(file=report)
            writer.writerow(
                [
                    str(curr_date),
                ]
            )
            writer.writerow([])

            for user, entries in records.items():
                total_road, total_obj, total_office = [], [], []
                print("-" * 50, file=report)
                print(user, file=report)
                writer.writerow([user, ""])

                for i in range(1, len(entries)):
                    prev, curr = entries[i - 1], entries[i]
                    time_spent = curr["dttm"] - prev["dttm"]
                    prev_obj, curr_obj = (
                        prev["record"].rsplit(" ", 1)[0],
                        curr["record"].rsplit(" ", 1)[0],
                    )

                    if "приехал" in prev["record"].lower():
                        summary = ""
                        if any(i == "Офис" for i in (prev_obj, curr_obj)):
                            total_office.append(time_spent)
                        else:
                            total_obj.append(time_spent)
                            recom_time = next(
                                (
                                    i["recom_time"]
                                    for i in tasks[user]
                                    if i["name"] in (prev_obj, curr_obj)
                                ),
                                None,
                            )
                            if recom_time:
                                summary += f" ({recom_time}ч.)"
                                if time_spent.total_seconds() / 3600 > recom_time:
                                    summary += " ПРЕВЫШЕНО!"

                        print(f"    {curr_obj}", file=report)
                        print(
                            f'        {str(prev["dttm"]).split()[1]}: {prev["record"].rsplit(" ", 1)[1]}',
                            file=report,
                        )
                        print(
                            f'        {str(curr["dttm"]).split()[1]}: {curr["record"].rsplit(" ", 1)[1]}',
                            file=report,
                        )
                        print(
                            f"        {time_spent}ч. на объекте {summary}", file=report
                        )

                    else:
                        print(
                            "            ----------",
                            f"        {time_spent} в дороге",
                            "            ----------",
                            sep="\n",
                            file=report,
                        )
                        total_road.append(time_spent)

                    print(file=report)

                # Запись итоговой информации
                write_summary(writer, report, total_road, total_obj, total_office)
                print(file=report)
                writer.writerow([])

    curr_date = datetime.now().date()  # - timedelta(days=1)
    # Получение данных и вызов основных функций
    data = JournalService.get_records(data={"date": curr_date})
    records, tasks = process_records(data)

    generate_report(records, tasks)

    root_folder = "Telegram/Reports"  # Корневая папка на Яндекс.Диске
    for suff in ["csv", "txt"]:
        file_name = f"{curr_date}." + suff
        yandex_disk_path = get_yandex_disk_path(file_name, root_folder, curr_date)

        # Загружаем файл на Яндекс.Диск
        # ensure_directories_exist(yandex_disk_path)
        # upload_to_yandex_disk(file_name, yandex_disk_path)
