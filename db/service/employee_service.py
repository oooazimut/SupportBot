from sqlite3 import Connection

from db.tools import connector


@connector
def new(con: Connection, userid: int, username: str, position: str):
    params = [userid, username, position]
    query = """
    INSERT INTO employees(userid, username, position) 
         VALUES (?, ?, ?)
    """
    con.execute(query, params)


@connector
def get_one(con: Connection, userid: str | int) -> dict | None:
    query = """
    SELECT * 
      FROM employees 
     WHERE userid = ?
    """
    return con.execute(query, [userid]).fetchone()


@connector
def get_all(con: Connection) -> list:
    data = con.execute("SELECT * FROM employees").fetchall()
    return data


@connector
def get_by_filters(con: Connection, **kwargs):
    """фильтры: position, username"""
    sub_query = " AND ".join(f"{item} = :{item}" for item in kwargs)
    query = f"SELECT * FROM employees WHERE {sub_query}"
    return con.execute(query, kwargs).fetchall()
