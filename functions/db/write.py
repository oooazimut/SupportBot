from sqlite3 import Connection

from functions.db.base import db_connector


@db_connector
def add_employee(con: Connection, userid: int, username: str, status: str):
    con.execute('INSERT INTO employees(id, username, status) VALUES (?, ?, ?)', (userid, username, status))
    con.commit()


@db_connector
def save_task(con: Connection, title, description, phone) -> int:
    con.execute('INSERT INTO tasks(phone, title, description, status, priority) VALUES (?, ?, ?, ?, ?)',
                (phone, title, description, 'opened', 'low'))
    taskid = con.execute('SELECT MAX(id) FROM tasks').fetchone()[0]
    con.commit()
    return taskid
