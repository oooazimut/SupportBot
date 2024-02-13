from db import task_service

data = task_service.get_tasks_by_status('назначено', userid=5963726977)

for i in data:
    print(i)