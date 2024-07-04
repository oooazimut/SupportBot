from db.models import DataBase, SqLiteDataBase
from db.schema import DB_NAME, CREATE_DB_SCRIPT

db = SqLiteDataBase(DB_NAME, CREATE_DB_SCRIPT)


class TaskService:
    def __init__(self, database: DataBase):
        self.database = database

    def save_task(self, task: dict):
        query = ('INSERT INTO tasks (created, creator, phone, title, description, media_type, media_id, status, '
                 'priority, act, entity, slave, agreement) VALUES (:created, :creator, :phone, :title, :description, '
                 ':media_type, :media_id, :status, :priority, :act, :entity, :slave, :agreement) RETURNING *')
        return self.database.post_query(query, task)

    def update_task(self, task: dict):
        query = ('UPDATE tasks SET (phone, title, description, media_type, media_id, status, priority, act, entity, '
                 'slave, agreement) = (:phone, :title, :description, :media_type, :media_id, :status, :priority, '
                 ':act, :entity, :slave, :agreement) WHERE taskid = :taskid RETURNING *')
        return self.database.post_query(query, task)

    def update_summary(self, taskid: int, summary: str):
        query = 'UPDATE tasks SET summary = ? where taskid = ?'
        return self.database.post_query(query, [summary, taskid])

    def get_task(self, taskid) -> list:
        # return self.database.select_query('SELECT * FROM tasks WHERE id = ?', [taskid])
        query = '''
        SELECT *
        FROM tasks as t
        LEFT JOIN entities as e
        ON e.ent_id = t.entity
        LEFT JOIN employees as em
        ON em.userid = t.slave
        WHERE t.taskid = ?
        '''
        return self.database.select_query(query, [taskid])

    def get_tasks(self):
        return self.database.select_query('SELECT * FROM tasks', params=None)

    def get_tasks_by_status(self, status, userid=None) -> list:
        finish = 'order by created DESC LIMIT 50'
        query = '''
        SELECT *
        FROM tasks as t
        LEFT JOIN employees as em
        ON em.userid = t.slave
        LEFT JOIN entities as en
        ON en.ent_id = t.entity
        WHERE t.status = ?
        '''
        if userid:
            query += ' AND t.slave = ?'
            result = self.database.select_query(query + finish, [status, userid])
        else:
            result = self.database.select_query(query + finish, [status])
        result.reverse()
        return result

    def get_archive_tasks(self, clientid):
        query = '''
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
        '''
        return self.database.select_query(query, [clientid, clientid])

    def get_active_tasks(self, userid):
        query = '''
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
        '''
        return self.database.select_query(query, [userid, userid])

    def change_priority(self, task_id):
        data = self.database.select_query('SELECT priority FROM tasks WHERE taskid = ?', [task_id])
        if data[0]['priority']:
            priority = ''
        else:
            priority = '\U0001F525'
        self.database.post_query('UPDATE tasks SET priority = ? WHERE taskid = ?', [priority, task_id])

    def change_status(self, task_id, status: str):
        self.database.post_query('UPDATE tasks SET status = ? WHERE taskid = ?', [status, task_id])

    def change_worker(self, task_id, slave):
        self.database.post_query('UPDATE tasks SET slave = ? WHERE taskid = ?', [slave, task_id])

    def get_tasks_for_entity(self, entity: str):
        query = '''
        SELECT *
        FROM tasks as t
        JOIN entities as e
        ON t.entity = e.ent_id
        WHERE e.name LIKE ? 
        '''
        self.database.select_query(query, [f'%{entity}%'])

    def get_task_reminder(self):
        data = self.database.select_query(
            '''SELECT * from tasks
             where priority="\U0001F525" 
             AND 
             slave is NOT NULL
             AND
             status NOT IN ('закрыто', 'выполнено', 'в работе', 'отложено')
             ''', params=None)
        return data

    def get_task_reminder_for_morning(self):
        data = self.database.select_query(
            '''SELECT * from tasks
             where slave is NOT NULL
             AND status NOT IN ('закрыто', 'выполнено', 'отложено')
             ''', params=None)
        return data

    def save_result(self, result, resultid, resulttype, taskid):
        params = [result, resulttype, resultid, taskid]
        self.database.post_query("UPDATE tasks SET result=?, resulttype=?, resultid=? WHERE taskid=?", params)

    def add_act(self, params: dict):
        query = 'UPDATE tasks SET actid = :actid, acttype = :acttype WHERE taskid = :taskid'
        self.database.post_query(query, params)


class EmployeeService:
    def __init__(self, database: DataBase):
        self.database = database

    def save_employee(self, userid: int, username: str, position: str):
        params = [userid, username, position]
        self.database.post_query('INSERT INTO employees(userid, username, position) VALUES (?, ?, ?)', params)

    def get_employee(self, userid):
        employee = self.database.select_query('SELECT * FROM employees WHERE userid = ?', [userid])
        if employee:
            return employee[0]

    def get_employees(self):
        data = self.database.select_query('SELECT * FROM employees', params=None)
        return data

    def get_employees_by_position(self, position):
        data = self.database.select_query('SELECT * FROM employees WHERE position = ?', [position])
        return data


class EntityService:

    @staticmethod
    def get_entities_by_substr(substr):
        query = 'SELECT * FROM entities WHERE MY_LOWER(name) LIKE MY_LOWER(?)'
        return db.select_query(query, [f'%{substr}%'])

    @staticmethod
    def get_task_for_entity(entity):
        query = 'SELECT * FROM tasks WHERE entity = ?'
        return db.select_query(query, [entity])

    @staticmethod
    def get_entity(entid):
        query = 'SELECT * FROM entities WHERE ent_id = ?'
        return db.select_query(query, [entid])

    @staticmethod
    def get_all_entities():
        return db.select_query('select * from entities')
