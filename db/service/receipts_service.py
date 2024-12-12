from sqlite3 import Connection

from db.tools import connector


@connector
def new(con: Connection, data: dict):
    query = """
    INSERT INTO receipts (dttm, employee, receipt, caption) 
         VALUES (:dttm, :employee, :receipt, :caption)
    """
    con.execute(query, data)
    con.commit()


@connector
def get_by_filters(con: Connection, **kwargs) -> list:
    """фильтры: dttm, employee"""

    adds = list()
    if kwargs.get("dttm"):
        adds.append("DATE(dttm) = :dttm")
    if kwargs.get("employee"):
        adds.append("employee = :employee")

    sub_query = "WHERE " + " AND ".join(adds)
    query = f"SELECT * FROM receipts {sub_query}"
    return con.execute(query, kwargs).fetchall()

@connector
def get_all(con: Connection):
    return con.execute('SELECT * FROM receipts')
