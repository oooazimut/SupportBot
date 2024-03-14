from db import db


data = db.select_query('select * from entities')
tasks = db.select_query('select * from tasks')
print(tasks)
print(data)