a = dict()
a.setdefault('a', 15)
a.setdefault('a', 24)
print(a)


def is_exist(task: dict):
    return task.get('taskid') is not None


print(is_exist(a))
