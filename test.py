from db import task_service

MY_ID = 5963726977

tasks = task_service.get_tasks()
for task in tasks:
    task_service.change_status(task['taskid'], 'открыто')
