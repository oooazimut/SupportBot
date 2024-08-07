from db.service import TaskService


tasks = TaskService.get_tasks_by_status('октрыто')
for i in tasks:
    TaskService.change_status(i['taskid'], 'открыто')
