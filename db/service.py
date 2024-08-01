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
    def update_task(task: dict):
        query = (
            "UPDATE tasks SET (phone, title, description, media_type, media_id, status, priority, act, entity, "
            "slave, agreement) = (:phone, :title, :description, :media_type, :media_id, :status, :priority, "
            ":act, :entity, :slave, :agreement) WHERE taskid = :taskid RETURNING *"
        )
        return SqDB.post_query(query, task)

    @staticmethod
    def update_summary(taskid: int, summary: str):
        query = "UPDATE tasks SET summary = ? where taskid = ?"
        return SqDB.post_query(query, [summary, taskid])

    @staticmethod
    def get_task(taskid) -> list:
        # return SqDB.select_query('SELECT * FROM tasks WHERE id = ?', [taskid])
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
    def get_tasks_by_status(status, userid=None) -> list:
        finish = "order by created DESC LIMIT 50"
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
            "UPDATE tasks SET priority = ? WHERE taskid = ?", [priority, task_id]
        )

    @staticmethod
    def change_status(task_id, status: str):
        SqDB.post_query(
            "UPDATE tasks SET status = ? WHERE taskid = ?", [status, task_id]
        )

    @staticmethod
    def change_worker(task_id, slave):
        SqDB.post_query("UPDATE tasks SET slave = ? WHERE taskid = ?", [slave, task_id])

    @staticmethod
    def get_tasks_for_entity(entity: str):
        query = """
        SELECT *
        FROM tasks as t
        JOIN entities as e
        ON t.entity = e.ent_id
        WHERE e.name LIKE ? 
        """
        SqDB.select_query(query, [f"%{entity}%"])

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

    @staticmethod
    def save_result(result, resultid, resulttype, taskid):
        params = [result, resulttype, resultid, taskid]
        SqDB.post_query(
            "UPDATE tasks SET result=?, resulttype=?, resultid=? WHERE taskid=?", params
        )

    @staticmethod
    def add_act(params: dict):
        query = (
            "UPDATE tasks SET actid = :actid, acttype = :acttype WHERE taskid = :taskid"
        )
        SqDB.post_query(query, params)

    @classmethod
    def reopen(cls, taskid: int | str):
        task = cls.get_task(taskid)[0]
        cls.save_task(task)


class EmployeeService:
    @staticmethod
    def save_employee(userid: int, username: str, position: str):
        params = [userid, username, position]
        SqDB.post_query(
            "INSERT INTO employees(userid, username, position) VALUES (?, ?, ?)", params
        )

    @staticmethod
    def get_employee(userid) -> dict|None:
        employee = SqDB.select_query(
            "SELECT * FROM employees WHERE userid = ?", [userid]
        )
        if employee:
            return employee[0]

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
    def get_task_for_entity(entity):
        query = "SELECT * FROM tasks WHERE entity = ?"
        return SqDB.select_query(query, [entity])

    @staticmethod
    def get_entity(entid):
        query = "SELECT * FROM entities WHERE ent_id = ?"
        return SqDB.select_query(query, [entid])
