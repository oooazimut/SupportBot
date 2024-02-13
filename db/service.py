from db.db_models import DataBase


class TaskService:
    def __init__(self, database: DataBase):
        self.database = database

    def save_task(self, params):
        query = ('INSERT INTO tasks(created, creator, phone, title, description, status, priority)'
                 ' VALUES (?, ?, ?, ?, ?, ?, ?)')
        self.database.post_query(query=query, params=params)

    def get_tasks(self):
        return self.database.select_query('SELECT * FROM tasks', params=None)

    def get_tasks_by_status(self, status, userid=None):
        if userid:
            return self.database.select_query('SELECT * FROM tasks WHERE status = ? AND slave = ?', [status, userid])
        return self.database.select_query('SELECT * FROM tasks WHERE status = ?', [status])

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

    def change_priority(self, task_id, priority):
        pass

    def get_archive_tasks(self, userid):
        query = '''
        SELECT * 
        FROM entities 
        JOIN tasks 
        ON tasks.entity = entities.id 
        WHERE tasks.creator = ?
        AND tasks.status = 'закрыто'
        AND tasks.entity = (SELECT entity 
                            FROM tasks 
                            WHERE creator = ? AND entity IS NOT NULL
                            ORDER BY id DESC LIMIT 1)
        '''
        return self.database.select_query(query, [userid, userid])


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
