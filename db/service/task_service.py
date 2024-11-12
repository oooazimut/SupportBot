from datetime import datetime
from sqlite3 import Connection

from db.tools import connector


@connector
def save_task(con: Connection, task: dict):
    query = (
        "INSERT INTO tasks (created, creator, phone, title, description, media_type, media_id, status, "
        "priority, act, entity, slave, agreement, simple_report, recom_time) VALUES (:created, :creator, :phone, :title, :description, "
        ":media_type, :media_id, :status, :priority, :act, :entity, :slave, :agreement, :simple_report, :recom_time) RETURNING *"
    )
    result = con.execute(query, task).fetchone()
    con.commit()
    return result


@connector
def remove_task(con: Connection, taskid):
    query = "DELETE FROM tasks WHERE taskid = ?"
    con.execute(query, [taskid])
    con.commit()


@connector
def update_task(con: Connection, task: dict):
    query = (
        "UPDATE tasks SET (created, phone, title, description, media_type, media_id, status, priority, act, entity, "
        "slave, agreement, simple_report, recom_time) = (:created, :phone, :title, :description, :media_type, :media_id, :status, :priority, "
        ":act, :entity, :slave, :agreement, :simple_report, :recom_time) WHERE taskid = :taskid RETURNING *"
    )
    result = con.execute(query, task).fetchone()
    con.commit()
    return result


@connector
def get_task(con: Connection, taskid) -> list:
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
def get_tasks(con: Connection):
    return con.execute("SELECT * FROM tasks").fetchall()


@connector
def get_tasks_with_filters(con: Connection, data: dict = {}):
    query = """
       SELECT *
         FROM tasks as t
    LEFT JOIN employees as em
           ON em.userid = t.slave
    LEFT JOIN entities as en
           ON en.ent_id = t.entity
    """
    params = list()
    adds = list()
    if data.get("entid"):
        adds.append("t.entity = ?")
        params.append(data.get("entid"))
    if data.get("userid"):
        adds.append("t.slave = ?")
        params.append(data.get("userid"))
    if data.get("date"):
        adds.append("DATE(t.created) = ?")
        params.append(data.get("date"))
    if data.get("status"):
        adds.append("t.status = ?")
        params.append(data.get("status"))
    if adds:
        query = query + " WHERE " + " AND ".join(adds)
    query += " ORDER BY created DESC"
    return con.execute(query, params).fetchall()


@connector
def get_tasks_by_status(con: Connection, status, userid=None) -> list:
    finish = "ORDER BY created"
    query = """
    SELECT *
    FROM tasks as t
    LEFT JOIN employees as em
    ON em.userid = t.slave
    LEFT JOIN entities as en
    ON en.ent_id = t.entity
    WHERE t.status = ?
    """
    if userid:
        query += " AND t.slave = ?"
        result = con.execute(query + finish, [status, userid]).fetchall()
    else:
        result = con.execute(query + finish, [status]).fetchall()
    result.reverse()
    return result


@connector
def get_archive_tasks(con: Connection, clientid):
    query = """
    SELECT * 
    FROM entities as e
    JOIN tasks as t
    ON t.entity = e.ent_id
    WHERE t.creator = ?
    AND t.status = 'закрыто'
    AND t.entity = (SELECT entity
                    FROM tasks
                    WHERE creator = ? AND entity IS NOT NULL
                    ORDER BY id DESC LIMIT 1)
    """
    return con.execute(query, [clientid, clientid]).fetchall()


@connector
def get_active_tasks(con: Connection, userid):
    query = """
    SELECT * 
    FROM entities 
    JOIN tasks 
    ON tasks.entity = entities.ent_id 
    WHERE tasks.creator = ?
    AND tasks.status != 'закрыто'
    AND tasks.entity = (SELECT entity 
                        FROM tasks 
                        WHERE creator = ? AND entity IS NOT NULL
                        ORDER BY id DESC LIMIT 1)
    """
    return con.execute(query, [userid, userid]).fetchall()


@connector
def change_priority(con: Connection, task_id):
    data = con.execute(
        "SELECT priority FROM tasks WHERE taskid = ?", [task_id]
    ).fetchone()
    if data["priority"]:
        priority = ""
    else:
        priority = "\U0001f525"
    con.execute(
        "UPDATE tasks SET priority = ? WHERE taskid = ?",
        [priority, task_id],
    )
    con.commit()


@connector
def change_status(con: Connection, task_id, status: str):
    con.execute(
        "UPDATE tasks SET status = ? WHERE taskid = ?",
        [status, task_id],
    )
    con.commit()


@connector
def change_worker(con: Connection, task_id, slave):
    con.execute("UPDATE tasks SET slave = ? WHERE taskid = ?", [slave, task_id])
    con.commit()


@connector
def get_tasks_for_entity(con: Connection, entid):
    query = """
    SELECT *
    FROM tasks as t
    LEFT JOIN employees as em
    ON em.userid = t.slave
    LEFT JOIN entities as en
    ON en.ent_id = t.entity
    WHERE t.entity = ?
    """
    return con.execute(query, [entid]).fetchall()


@connector
def update_result(con: Connection, resultid, taskid):
    old_result = get_task(taskid).get("resultid")
    if old_result:
        resultid += f",{old_result}"

    con.execute(
        "UPDATE tasks SET resultid=? WHERE taskid=?",
        [resultid, taskid],
    )
    con.commit()


@connector
def add_act(con: Connection, params: dict):
    actid = get_task(params["taskid"]).get("actid")
    if actid:
        params["actid"] += f",{actid}"

    query = "UPDATE tasks SET actid = :actid WHERE taskid = :taskid"
    con.execute(query, params)
    con.commit()


@connector
def reopen_task(con: Connection, taskid):
    task = get_task(taskid)
    task["created"] = datetime.now().replace(microsecond=0)
    task["status"] = "назначено"
    task["slave"] = None
    save_task(task)


@connector
def change_dttm(con: Connection, taskid, dttm):
    query = "UPDATE tasks SET created = ? WHERE taskid = ?"
    con.execute(query, [dttm, taskid])
    con.commit()

@connector
def clone_task(con, taskid):
    task = get_task((taskid))
    task['created'] = datetime.now().replace(microsecond=0)
    task['status'] = 'открыто'
    for item in ('slave', 'resultid', 'actid'):
        task[item] = None
    save_task(task)
