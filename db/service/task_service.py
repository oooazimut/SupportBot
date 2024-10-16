from datetime import datetime
from ..models import SqLiteDataBase as SqDB


def save_task(task: dict):
    query = (
        "INSERT INTO tasks (created, creator, phone, title, description, media_type, media_id, status, "
        "priority, act, entity, slave, agreement, simple_report, recom_time) VALUES (:created, :creator, :phone, :title, :description, "
        ":media_type, :media_id, :status, :priority, :act, :entity, :slave, :agreement, :simple_report, :recom_time) RETURNING *"
    )
    return SqDB.post_query(query, task)


def remove_task(taskid):
    query = "DELETE FROM tasks WHERE taskid = ? RETURNING *"
    SqDB.post_query(query, [taskid])


def update_task(task: dict):
    query = (
        "UPDATE tasks SET (created, phone, title, description, media_type, media_id, status, priority, act, entity, "
        "slave, agreement, simple_report, recom_time) = (:created, :phone, :title, :description, :media_type, :media_id, :status, :priority, "
        ":act, :entity, :slave, :agreement, :simple_report, :recom_time) WHERE taskid = :taskid RETURNING *"
    )
    return SqDB.post_query(query, task)


def get_task(taskid) -> list:
    query = """
    SELECT *
    FROM tasks as t
    LEFT JOIN entities as e
    ON e.ent_id = t.entity
    LEFT JOIN employees as em
    ON em.userid = t.slave
    WHERE t.taskid = ?
    """
    return SqDB.select_query(query, [taskid])


def get_tasks():
    return SqDB.select_query("SELECT * FROM tasks", params=None)


def get_tasks_with_filters(data: dict = {}):
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
    return SqDB.select_query(query, params)


def get_tasks_by_status(status, userid=None) -> list:
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
        result = SqDB.select_query(query + finish, [status, userid])
    else:
        result = SqDB.select_query(query + finish, [status])
    result.reverse()
    return result


def get_archive_tasks(clientid):
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
    return SqDB.select_query(query, [clientid, clientid])


def get_active_tasks(userid):
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
    return SqDB.select_query(query, [userid, userid])


def change_priority(task_id):
    data = SqDB.select_query("SELECT priority FROM tasks WHERE taskid = ?", [task_id])
    if data[0]["priority"]:
        priority = ""
    else:
        priority = "\U0001f525"
    SqDB.post_query(
        "UPDATE tasks SET priority = ? WHERE taskid = ? RETURNING *",
        [priority, task_id],
    )


def change_status(task_id, status: str):
    SqDB.post_query(
        "UPDATE tasks SET status = ? WHERE taskid = ? RETURNING *",
        [status, task_id],
    )


def change_worker(task_id, slave):
    SqDB.post_query(
        "UPDATE tasks SET slave = ? WHERE taskid = ? RETURNING *", [slave, task_id]
    )


def get_tasks_for_entity(entid):
    query = """
    SELECT *
    FROM tasks as t
    LEFT JOIN employees as em
    ON em.userid = t.slave
    LEFT JOIN entities as en
    ON en.ent_id = t.entity
    WHERE t.entity = ?
    """
    return SqDB.select_query(query, [entid])


def get_task_reminder() -> list:
    data = SqDB.select_query(
        """SELECT * from tasks
         where priority="\U0001f525" 
         AND 
         slave is NOT NULL
         AND
         status NOT IN ('закрыто', 'выполнено', 'в работе', 'отложено')
         """,
        params=None,
    )
    return data


def get_task_reminder_for_morning():
    data = SqDB.select_query(
        """SELECT * from tasks
         where slave is NOT NULL
         AND status NOT IN ('закрыто', 'выполнено', 'отложено')
         """,
        params=None,
    )
    return data


def update_result(resultid, taskid):
    old_result = get_task(taskid)[0].get("resultid")
    if old_result:
        resultid += f",{old_result}"

    SqDB.post_query(
        "UPDATE tasks SET resultid=? WHERE taskid=? RETURNING *",
        [resultid, taskid],
    )


def add_act(params: dict):
    actid = get_task(params["taskid"])[0].get("actid")
    if actid:
        params["actid"] += f",{actid}"

    query = "UPDATE tasks SET actid = :actid WHERE taskid = :taskid RETURNING *"
    SqDB.post_query(query, params)


def reopen_task(taskid):
    task = get_task(taskid)[0]
    task["created"] = datetime.now().replace(microsecond=0)
    task["status"] = "назначено"
    task["slave"] = None
    save_task(task)


def change_dttm(taskid, dttm):
    query = "UPDATE tasks SET created = ? WHERE taskid = ? RETURNING *"
    SqDB.post_query(query, [dttm, taskid])
