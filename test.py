from db.db_models import SqLiteDataBase
from db.service import TaskService
from db.service import EmployeeService

db = SqLiteDataBase('Support.db')

ts = TaskService(db)
# ts.save_task([datetime.datetime.now(), 'Petya', 999999, 'zopa_polnaya', 'alarm', 'opened', 'low'])
b = ts.get_tasks()
es = EmployeeService(db)
# es.save_employee([1, 'Sergey', 'worker'])
e = es.get_employees()
print(es.get_employee(2)['id'])
