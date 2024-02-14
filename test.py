import datetime

from db import task_service


data = task_service.get_task(1)
# print(data)
dt = '2024-02-12 09:14:41.939450'
print(dt.split('.')[0])
