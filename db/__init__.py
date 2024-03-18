from db.models import SqLiteDataBase
from db.service import EmployeeService, TaskService


db = SqLiteDataBase('Support.db')
empl_service = EmployeeService(db)
task_service = TaskService(db)
