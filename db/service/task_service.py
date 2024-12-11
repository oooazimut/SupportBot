from datetime import datetime
from sqlite3 import Connection

from config import TasksStatuses
from db.tools import connector


@connector
def new(con: Connection, **kwargs):
    query = """
    INSERT INTO tasks (
        created, creator, phone, title, description, 
        media_type, media_id, status, priority, act, 
        entity, slave, agreement, simple_report, recom_time
        ) 
         VALUES (
        :created, :creator, :phone, :title, :description, 
        :media_type, :media_id, :status, :priority, :act, 
        :entity, :slave, :agreement, :simple_report, :recom_time
        ) 
      RETURNING *
    """
    result = con.execute(query, kwargs).fetchone()
    con.commit()
    return result


@connector
def delete(con: Connection, taskid):
    query = "DELETE FROM tasks WHERE taskid = ?"
    con.execute(query, [taskid])
    con.commit()


@connector
def update(con: Connection, **kwargs):
    taskid = kwargs.pop("taskid")
    sub_query = ", ".join(f"{item} = :{item}" for item in kwargs)
    kwargs.update(taskid=taskid)
    query = f"""
        UPDATE tasks 
           SET {sub_query} 
         WHERE taskid = :taskid
     RETURNING *
     """
    result = con.execute(query, kwargs).fetchone()
    con.commit()
    return result


@connector
def get_one(con: Connection, taskid) -> list:
    query = """
       SELECT *
         FROM tasks as t
    LEFT JOIN entities as e
           ON e.ent_id = t.entity
    LEFT JOIN employees as em
           ON em.userid = t.slave
        WHERE t.taskid = ?
    """
    return con.execute(query, [taskid]).fetchone()


@connector
def get_all(con: Connection):
    return con.execute("SELECT * FROM tasks").fetchall()


@connector
def get_by_filters(con: Connection, **kwargs):
    """фильтрация по entid(объект), userid(исполнитель),
    date(дата создания), status, creator, current(не в архиве)
    """
    query = """
       SELECT *
         FROM tasks as t
    LEFT JOIN employees as em
           ON em.userid = t.slave
    LEFT JOIN entities as en
           ON en.ent_id = t.entity
    """
    adds = list()
    if kwargs.get("entid"):
        adds.append("t.entity = :entid")
    if kwargs.get("userid"):
        adds.append("t.slave = :userid")
    if kwargs.get("date"):
        adds.append("DATE(t.created) = :date")
    if kwargs.get("status"):
        adds.append("t.status = :status")
    if kwargs.get("creator"):
        adds.append("t.creator = :creator")
    if kwargs.get("current"):
        adds.append(f"t.status != '{TasksStatuses.ARCHIVE}'")
    if adds:
        query = query + " WHERE " + " AND ".join(adds)
    query += " ORDER BY created DESC"
    return con.execute(query, kwargs).fetchall()


def reopen_task(taskid):
    task = get_one(taskid)
    task.update(
        created=datetime.now().replace(microsecond=0),
        status=TasksStatuses.ASSIGNED,
        slave=None,
    )
    new(**task)


def clone_task(taskid):
    task = get_one((taskid))
    task.update(
        created=datetime.now().replace(microsecond=0),
        status=TasksStatuses.OPENED,
    )
    task.update({key: None for key in ("slave", "resultid", "actid")})
    new(**task)


@connector
def get_keys(con: Connection):
    query = "SELECT * FROM tasks ORDER BY taskid DESC LIMIT 1"
    result = con.execute(query).fetchone()
    return set(result.keys())
