from db.models import DataBase, SqLiteDataBase
from db.schema import DB_NAME, CREATE_DB_SCRIPT

db = SqLiteDataBase(DB_NAME, CREATE_DB_SCRIPT)


class TaskService:
    def __init__(self, database: DataBase):
        self.database = database

    def save_task(self, created, creator, phone, title, description, media_type, media_id, status, priority, entity,
                  slave):
        params = [created, creator, phone, title, description, media_type, media_id, status, priority, entity, slave]
        query = '''
        INSERT INTO tasks(created, creator, phone, title, description, media_type, media_id, status, priority,
                        entity, slave)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        self.database.post_query(query=query, params=params)

    def update_task(self, phone, title, description, media_type, media_id, status, priority, entity, slave, taskid):
        params = [phone, title, description, media_type, media_id, status, priority, entity, slave, taskid]
        query = '''UPDATE tasks SET (phone, title, description, media_type, media_id, status, priority, entity, 
        slave) = (?, ?, ?, ?, ?, ?, ?, ?, ?) WHERE taskid = ?'''
        self.database.post_query(query, params)

    def get_task(self, taskid):
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
        query = '''
        SELECT *
        FROM tasks as t
        LEFT JOIN employees as em
        ON em.userid = t.slave
        WHERE t.status = ? 
        '''
        if userid:
            query += ' AND t.slave = ?'
            return self.database.select_query(query, [status, userid])
        return self.database.select_query(query, [status])

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
             ''', params=None)
        return data

    def get_task_reminder_for_morning(self):
        data = self.database.select_query(
            '''SELECT * from tasks
             where slave is NOT NULL
             ''', params=None)
        return data


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
        query = 'SELECT * FROM task WHERE entities = ?'
        return db.select_query(query, [entity])
