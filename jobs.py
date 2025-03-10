import csv
import logging
from collections import defaultdict
from datetime import datetime, timedelta

from aiogram.types import Message

from config import CONTENT_ATTR_MAP
from db.service import employee_service, journal_service
from yandex import ensure_directories_exist, get_yandex_disk_path, upload_to_yandex_disk

logger = logging.getLogger(__name__)


async def two_reports():
    curr_date = datetime.now().date() - timedelta(days=1)
    # curr_date = date(2024, 11, 10)

    def process_records(data):
        """Функция обработки записей."""
        keys = ["username", "record", "dttm", "name", "recom_time", "task"]
        roadwords = ["приехал", "уехал"]

        road = [
            rec
            for rec in data
            if any(word in rec["record"].lower() for word in roadwords)
        ]

        tasks = [rec for rec in data if rec["recom_time"] and rec["username"]]

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
        for entry in sorted(processed_data, key=lambda x: x["dttm"]):
            grouped_road[entry["username"]].append(entry)
        grouped_tasks = defaultdict(list)
        for entry in sorted(tasks, key=lambda x: x["dttm"]):
            grouped_tasks[entry["username"]].append(entry)

        users = employee_service.get_all()
        users = [
            user
            for user in users
            if user["username"] not in ["Директор", "Надежда Половинкина", "Роберт"]
        ]
        for user in users:
            grouped_road.setdefault(user["username"], [])

        grouped_road = dict(
            sorted(grouped_road.items(), key=lambda x: x[0].split()[-1])
        )

        return grouped_road, grouped_tasks

    def write_summary(writer, report, total_road, total_obj, total_office):
        """Вывод общей информации по времени."""
        if any(lst for lst in (total_road, total_obj, total_office)):
            print("  Общее время:", file=report)
            writer.writerow(["", "Общее время:"])

        for name, times in (
            ("Офис", total_office),
            ("Объекты", total_obj),
            ("Дорога", total_road),
        ):
            total_time = sum(times, timedelta())
            if total_time:
                print(f"    {name}: {total_time}", file=report)
                writer.writerow(["", name, total_time])

    def generate_report(records, tasks, curr_date):
        """Генерация текстового и CSV отчета."""

        with (
            open(f"{curr_date}.txt", "w") as report,
            open(f"{curr_date}.csv", "w", encoding="cp1251", newline="") as csv_report,
        ):
            writer = csv.writer(csv_report, delimiter=";")

            print(curr_date, file=report)
            print(file=report)
            writer.writerow([
                str(curr_date),
            ])
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

                    if (
                        "приехал" in prev["record"].lower()
                        and "уехал" in curr["record"].lower()
                    ):
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
                            f"        {str(prev['dttm']).split()[1]}: {prev['record'].rsplit(' ', 1)[1]}",
                            file=report,
                        )
                        print(
                            f"        {str(curr['dttm']).split()[1]}: {curr['record'].rsplit(' ', 1)[1]}",
                            file=report,
                        )
                        print(
                            f"        {time_spent}ч. на объекте {summary}", file=report
                        )
                        writer.writerows([
                            ["", curr_obj],
                            [
                                "",
                                str(prev["dttm"]).split()[1],
                                prev["record"].rsplit(" ", 1)[1],
                            ],
                            [
                                "",
                                str(curr["dttm"]).split()[1],
                                curr["record"].rsplit(" ", 1)[1],
                            ],
                            ["", f"{time_spent}ч. на объекте {summary}"],
                        ])
                    elif (
                        "уехал" in prev["record"].lower()
                        and "приехал" in curr["record"].lower()
                    ):
                        print(
                            "            ----------",
                            f"        {time_spent} в дороге",
                            "            ----------",
                            sep="\n",
                            file=report,
                        )
                        writer.writerow(["", f"{time_spent} в дороге"])
                        total_road.append(time_spent)

                    else:
                        print('    Ошибка, нет пары "приехал-уехал":', file=report)
                        print(
                            f"        {str(prev['dttm']).split()[1]}: {prev['record']}",
                            file=report,
                        )
                        print(
                            f"        {str(curr['dttm']).split()[1]}: {curr['record']}",
                            file=report,
                        )
                        writer.writerows([
                            ["", 'Ошибка, нет пары "приехал-уехал":'],
                            ["", str(prev["dttm"]).split()[1], prev["record"]],
                            ["", str(curr["dttm"]).split()[1], curr["record"]],
                        ])
                    print(file=report)
                    writer.writerow([])

                # Запись итоговой информации
                write_summary(writer, report, total_road, total_obj, total_office)
                print(file=report)
                writer.writerow([])

    # Получение данных и вызов основных функций
    data = journal_service.get_by_filters(date=curr_date)
    records, tasks = process_records(data)

    generate_report(records, tasks, curr_date)

    root_folder = "Telegram/Reports"  # Корневая папка на Яндекс.Диске
    for suff in ["csv", "txt"]:
        file_name = f"{curr_date}." + suff
        yandex_disk_path = get_yandex_disk_path(file_name, root_folder, curr_date)

        # Загружаем файл на Яндекс.Диск
        ensure_directories_exist(yandex_disk_path)
        upload_to_yandex_disk(file_name, yandex_disk_path)


def handle_description(message: Message, data: dict):
    media_type = message.content_type
    media_id, description = CONTENT_ATTR_MAP[media_type](message)
    media_type = media_type.value if media_id else ""
    for key, value in zip(
        ("media_type", "media_id", "description"),
        (media_type, media_id, description),
    ):
        delimiter = "\n" if key == "description" else ","
        data[key] = f"{data.get(key, '')}{delimiter}{value}".strip(delimiter)
