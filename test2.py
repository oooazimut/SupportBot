import sqlite3
from db.service import TaskService


tasks = TaskService.get_tasks_for_entity(21)
opened_tasks = TaskService.get_tasks_by_status("открыто")


def human_output(data: list[dict] | None) -> None:
    if data:
        for i in data:
            for j, k in i.items():
                print(j, k)
            print()


human_output(tasks)
print()
human_output(opened_tasks)


with sqlite3.connect("Support.db") as con:
    a = con.execute("""
        SELECT *
        FROM tasks as t
        LEFT JOIN employees as em
        ON em.userid = t.slave
        LEFT JOIN entities as en
        ON en.ent_id = t.entity
        WHERE t.entity = ?
        """, [21]).fetchall()[0]

print(a)
