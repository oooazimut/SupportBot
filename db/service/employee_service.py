from sqlite3 import Connection

from db.tools import connector


@connector
def save_employee(con: Connection, userid: int, username: str, position: str):
    params = [userid, username, position]
    con.execute(
        "INSERT INTO employees(userid, username, position) VALUES (?, ?, ?)",
        params,
    )


@connector
def get_employee(con: Connection, userid: str | int) -> dict | None:
    employee = con.execute(
        "SELECT * FROM employees WHERE userid = ?", [userid]
    ).fetchone()
    return employee


@connector
def get_employees(con: Connection) -> list:
    data = con.execute("SELECT * FROM employees").fetchall()
    return data


@connector
def get_employees_by_position(con: Connection, position: str) -> list:
    data = con.execute(
        "SELECT * FROM employees WHERE position = ?", [position]
    ).fetchall()
    return data
