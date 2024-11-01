from sqlite3 import Connection

from db.tools import connector


@connector
def new_receipt(con: Connection, data: dict):
    query = "INSERT INTO receipts (dttm, employee, receipt, caption) VALUES (:dttm, :employee, :receipt, :caption)"
    con.execute(query, data)
    con.commit()


@connector
def get_receipts(con: Connection, params={}) -> list:
    query = "SELECT * FROM receipts"
    adds = list()
    if params.get("dttm"):
        adds.append("DATE(dttm) = :dttm")
    if params.get("employee"):
        adds.append("employee = :employee")

    if adds:
        query += " WHERE " + " AND ".join(adds)

    return con.execute(query, params).fetchall()
