from db import task_service


data = task_service.get_task('1')[0]
for key, value in data.items():
    print(key, value)