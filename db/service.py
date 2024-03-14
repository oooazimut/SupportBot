from db.db_models import DataBase


class TaskService:
    def __init__(self, database: DataBase):
        self.database = database

    def save_task(self, params):
        query = '''
        INSERT INTO tasks(
                        created,
                        creator, 
                        phone, 
                        title, 
                        client_info, 
                        media_type, 
                        media_id, 
                        status, 
                        priority)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        self.database.post_query(query=query, params=params)

    def get_task(self, taskid):
        # return self.database.select_query('SELECT * FROM tasks WHERE id = ?', [taskid])
        query = '''
        SELECT 
            t.id,
            t.created,
            t.creator,
            t.phone,
            t.title,
            t.description,
            t.status,
            t.priority,
            t.slave,
            e.name
        FROM tasks as t
        JOIN entities as e
        ON e.id = t.entity
        WHERE t.id = ?
        '''
        return self.database.select_query(query, [taskid])

    def get_tasks(self):
        return self.database.select_query('SELECT * FROM tasks', params=None)

    def get_tasks_by_status(self, status, userid=None) -> list:
        if userid:
            return self.database.select_query('SELECT * FROM tasks WHERE status = ? AND slave = ?', [status, userid])
        return self.database.select_query('SELECT * FROM tasks WHERE status = ?', [status])

    def get_archive_tasks(self, clientid):
        query = '''
        SELECT * 
        FROM entities as e
        JOIN tasks as t
        ON t.entity = e.id
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
        ON tasks.entity = entities.id 
        WHERE tasks.creator = ?
        AND tasks.status != 'закрыто'
        AND tasks.entity = (SELECT entity 
                            FROM tasks 
                            WHERE creator = ? AND entity IS NOT NULL
                            ORDER BY id DESC LIMIT 1)
        '''
        return self.database.select_query(query, [userid, userid])

    def change_priority(self, task_id):
        data = self.database.select_query('SELECT priority FROM tasks WHERE id = ?', [task_id])
        print(data)
        if data[0]['priority']:
            priority = ''
        else:
            priority = '\U0001F525'
        self.database.post_query('UPDATE tasks SET priority = ? WHERE id = ?', [priority, task_id])

    def change_status(self, task_id, status):
        self.database.post_query('UPDATE tasks SET status = ? WHERE id = ?', [status, task_id])

    def change_worker(self, task_id, slave):
        self.database.post_query('UPDATE tasks SET slave = ? WHERE id = ?', [slave, task_id])


class EmployeeService:
    def __init__(self, database: DataBase):
        self.database = database

    def save_employee(self, params):
        self.database.post_query('INSERT INTO employees(id, username, status) VALUES (?, ?, ?)', params)

    def get_employee(self, userid):
        employee = self.database.select_query('SELECT * FROM employees WHERE id = ?', [userid])
        if employee:
            return employee[0]

    def get_employees(self):
        data = self.database.select_query('SELECT * FROM employees', params=None)
        return data

    def get_employees_by_status(self, status):
        data = self.database.select_query('SELECT * FROM employees WHERE status = ?', [status])
        return data
