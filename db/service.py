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

    def get_tasks_by_period(self, params):
        pass

    def get_tasks_by_priority(self, params):
        pass



class EmployeeService:
    def __init__(self, database: DataBase):
        self.database = database

    def save_employee(self, params):
        self.database.post_query('INSERT INTO employees(id, username, status) VALUES (?, ?, ?)', params)

    def get_employee(self, userid):
        return self.database.select_query('SELECT * FROM employees WHERE id = ?', [userid])

    def get_employees(self):
        data = self.database.select_query('SELECT * FROM employees', params=None)
        return data
