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

    def get_tasks_by_status(self, status):
        return self.database.select_query('SELECT * FROM tasks WHERE status = ?', [status])

    def get_active_tasks(self, userid=None):
        query = '''
        select * 
        from entities 
        join tasks 
        on tasks.entity = entities.id 
        where tasks.creator = ?
        and tasks.entity = (select entity 
                            from tasks 
                            where creator = ? and status != 'opened'
                            order by id desc limit 1)
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
