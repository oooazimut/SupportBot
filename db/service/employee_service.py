from sqlite3 import Connection

from db.tools import connector


@connector
def save_employee(con: Connection, userid: int, username: str, position: str):
    params = [userid, username, position]
    query = """
    INSERT INTO employees(userid, username, position) 
         VALUES (?, ?, ?)
    """
    con.execute(query, params)


@connector
def get_employee(con: Connection, userid: str | int) -> dict | None:
    query = """
    SELECT * 
      FROM employees 
     WHERE userid = ?
    """
    employee = con.execute(query, [userid]).fetchone()
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
