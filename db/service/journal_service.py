from datetime import datetime
from sqlite3 import Connection

from db.tools import connector


@connector
def new(con: Connection, **kwargs):
    kwargs.setdefault("dttm", datetime.now().replace(microsecond=0))
    query = """
    INSERT INTO journal (dttm, employee, task, record) 
         VALUES (:dttm, :employee, :task, :record)
    """
    con.execute(query, kwargs)
    con.commit()


@connector
def get_all(con: Connection):
    return con.execute("SELECT * from journal").fetchall()


@connector
def get_by_filters(con: Connection, **kwargs) -> list:
    data = kwargs
    query = """
       SELECT *
         FROM journal as j
    LEFT JOIN employees as e 
           ON e.userid = j.employee
    LEFT JOIN tasks as t 
           ON t.taskid= j.task
    LEFT JOIN entities as ent 
           ON ent.ent_id =  t.entity 
    """
    adds = list()
    if data.get("userid"):
        adds.append("j.employee = :userid")
    if data.get("date"):
        adds.append("DATE(j.dttm) = :date")
    if data.get("taskid"):
        if data.get("taskid") == "null":
            adds.append("j.task IS NULL")
        else:
            adds.append("j.task = :taskid")
    if data.get("object"):
        adds.append("ent.name = :object")
    if data.get("record"):
        adds.append("j.record LIKE :record")

    if adds:
        query = query + " WHERE " + " AND ".join(adds)

    query += " ORDER BY created DESC"
    return con.execute(query, data).fetchall()


@connector
def get_last(con: Connection, userid: str | int) -> dict | None:
    curr_date = datetime.today().date()
    query = """
      SELECT * 
        FROM journal 
       WHERE employee = ? 
         AND DATE(dttm) = ? 
         AND (record LIKE "%Приехал" OR record LIKE "%Уехал") 
    ORDER BY dttm DESC LIMIT 1
    """
    return con.execute(query, [userid, curr_date]).fetchone()


def get_last_record(userid: str | int) -> str:
    result = get_last(userid)
    return result["record"] if result else ""


def get_last_record_id(userid) -> int:
    result = get_last(userid)
    return result["recordid"] if result else 0


@connector
def delete(con: Connection, recordid):
    query = "DELETE FROM journal WHERE recordid = ?"
    con.execute(query, [recordid])
    con.commit()
