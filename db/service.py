from datetime import datetime
from .models import SqLiteDataBase as SqDB


class TaskService:
    @staticmethod
    def save_task(task: dict):
        query = (
            "INSERT INTO tasks (created, creator, phone, title, description, media_type, media_id, status, "
            "priority, act, entity, slave, agreement) VALUES (:created, :creator, :phone, :title, :description, "
            ":media_type, :media_id, :status, :priority, :act, :entity, :slave, :agreement) RETURNING *"
        )
        return SqDB.post_query(query, task)

    @staticmethod
    def remove_task(taskid):
        query = "DELETE FROM tasks WHERE taskid = ? RETURNING *"
        SqDB.post_query(query, [taskid])

    @staticmethod
    def update_task(task: dict):
        query = (
            "UPDATE tasks SET (phone, title, description, media_type, media_id, status, priority, act, entity, "
            "slave, agreement) = (:phone, :title, :description, :media_type, :media_id, :status, :priority, "
            ":act, :entity, :slave, :agreement) WHERE taskid = :taskid RETURNING *"
        )
        return SqDB.post_query(query, task)

    @staticmethod
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

    @staticmethod
    def get_tasks():
        return SqDB.select_query("SELECT * FROM tasks", params=None)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def change_priority(task_id):
        data = SqDB.select_query(
            "SELECT priority FROM tasks WHERE taskid = ?", [task_id]
        )
        if data[0]["priority"]:
            priority = ""
        else:
            priority = "\U0001f525"
        SqDB.post_query(
            "UPDATE tasks SET priority = ? WHERE taskid = ? RETURNING *",
            [priority, task_id],
        )

    @staticmethod
    def change_status(task_id, status: str):
        SqDB.post_query(
            "UPDATE tasks SET status = ? WHERE taskid = ? RETURNING *",
            [status, task_id],
        )

    @staticmethod
    def change_worker(task_id, slave):
        SqDB.post_query(
            "UPDATE tasks SET slave = ? WHERE taskid = ? RETURNING *", [slave, task_id]
        )

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def get_task_reminder_for_morning():
        data = SqDB.select_query(
            """SELECT * from tasks
             where slave is NOT NULL
             AND status NOT IN ('закрыто', 'выполнено', 'отложено')
             """,
            params=None,
        )
        return data

    @classmethod
    def update_result(cls, resultid, taskid):
        old_result = cls.get_task(taskid)[0].get("resultid")
        if old_result:
            resultid += f",{old_result}"

        SqDB.post_query(
            "UPDATE tasks SET resultid=? WHERE taskid=? RETURNING *",
            [resultid, taskid],
        )

    @classmethod
    def add_act(cls, params: dict):
        actid = cls.get_task(params["taskid"])[0].get("actid")
        if actid:
            params["actid"] += f",{actid}"

        query = "UPDATE tasks SET actid = :actid WHERE taskid = :taskid RETURNING *"
        SqDB.post_query(query, params)


class EmployeeService:
    @staticmethod
    def save_employee(userid: int, username: str, position: str):
        params = [userid, username, position]
        SqDB.post_query(
            "INSERT INTO employees(userid, username, position) VALUES (?, ?, ?) RETURNING *",
            params,
        )

    @staticmethod
    def get_employee(userid) -> dict:
        employee = SqDB.select_query(
            "SELECT * FROM employees WHERE userid = ?", [userid]
        )
        if employee:
            return employee[0]
        else:
            return {}

    @staticmethod
    def get_employees():
        data = SqDB.select_query("SELECT * FROM employees", params=None)
        return data

    @staticmethod
    def get_employees_by_position(position):
        data = SqDB.select_query(
            "SELECT * FROM employees WHERE position = ?", [position]
        )
        return data


class EntityService:
    @staticmethod
    def get_entities_by_substr(substr):
        query = "SELECT * FROM entities WHERE MY_LOWER(name) LIKE MY_LOWER(?)"
        return SqDB.select_query(query, [f"%{substr}%"])

    @staticmethod
    def get_entity(entid):
        query = "SELECT * FROM entities WHERE ent_id = ?"
        return SqDB.select_query(query, [entid])


class JournalService:
    @staticmethod
    def new_record(data: dict):
        data["dttm"] = datetime.now().replace(microsecond=0)
        query = "INSERT INTO journal (dttm, employee, task, record) VALUES (:dttm, :employee, :task, :record) RETURNING *"
        return SqDB.post_query(query, data)

    @staticmethod
    def get_records(data: dict = {}):
        query = """
        SELECT *
        FROM journal as j
        LEFT JOIN employees as e ON e.userid = j.employee
        LEFT JOIN tasks as t ON t.taskid= j.task
        LEFT JOIN entities as ent ON ent.ent_id =  t.entity 
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

        if adds:
            query = query + " WHERE " + " AND ".join(adds)

        query += " ORDER BY created DESC"
        return SqDB.select_query(query, data)

    @staticmethod
    def del_record(recordid):
        query = "DELETE FROM journal WHERE recordid = ? RETURNING *"
        SqDB.post_query(query, [recordid])


class ReceiptsService:
    @staticmethod
    def new_receipt(data: dict):
        query = "INSERT INTO receipts (dttm, employee, receipt, caption) VALUES (:dttm, :employee, :receipt, :caption) RETURNING *"
        SqDB.post_query(query, data)

    @staticmethod
    def get_receipts(params={}):
        query = "SELECT * FROM receipts"
        adds = list()
        if params.get("dttm"):
            adds.append("DATE(dttm) = :dttm")
        if params.get("employee"):
            adds.append("employee = :employee")

        if adds:
            query += " WHERE " + " AND ".join(adds)

        return SqDB.select_query(query, params)
