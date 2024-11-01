import sqlite3
from db.service import entity_service

obj = entity_service.get_entity_by_name('Черкесская 4')

for k, v in obj.items():
    print(k, v)

with sqlite3.connect('Support.db') as con:
    con.execute('delete from entities where ent_id = 54')
    con.commit()
