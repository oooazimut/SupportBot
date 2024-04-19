from db import task_service

MY_ID = 5963726977

tasks = task_service.get_tasks()
for i in tasks:
    for key in i:
        print(key, i[key], type(i[key]))
    print()
