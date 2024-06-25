from db import task_service

data = task_service.get_tasks_by_status(';jsdfsad')
print(data, type(data))
print(data is not None)

def test():
    return bool(task_service.get_tasks_by_status('закрыто'))


a = test()

print(a, type(a))