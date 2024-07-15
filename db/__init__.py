from db.models import SqLiteDataBase
from db.schema import DB_NAME, CREATE_DB_SCRIPT
from db.service import EmployeeService, TaskService

db = SqLiteDataBase(DB_NAME, CREATE_DB_SCRIPT)

empl_service = EmployeeService(db)
task_service = TaskService(db)
