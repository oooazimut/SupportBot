from db import db
from db import task_service

query = '''
select * 
    from entities 
    join tasks 
    on tasks.entity = entities.id 
    where tasks.creator = 5963726977 
    and tasks.entity = (select entity 
                        from tasks 
                        where creator = 5963726977 and entity is not null 
                        order by id desc limit 1)
'''
data = task_service.get_active_tasks(5963726977)

archive = task_service.get_archive_tasks(5963726977)

for i in data:
    print(i)
print()
for i in archive:
    print(i)
