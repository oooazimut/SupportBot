from sqlite3 import Connection

from functions.db.base import db_connector

SELECT_USERS = 'SELECT * FROM users WHERE status = ?'


@db_connector
def get_employees(con: Connection):
    return con.execute('SELECT * FROM employees').fetchall()


@db_connector
def get_employee(con: Connection, userid: int):
    return con.execute('SELECT * FROM employees WHERE id = ?', (userid, )).fetchone()
