from db import db

query = '''
select * 
    from entities 
    join tasks 
    on tasks.entity = entities.id 
    where tasks.creator = 5963726977 
    and tasks.entity = (select entity 
                        from tasks 
                        where creator = 5963726977 and status != 'opened' 
                        order by id desc limit 1)
'''
data = db.select_query(query=query)

for i in data:
    print(i)
