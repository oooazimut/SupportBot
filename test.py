import sqlite3 as sq

MY_ID = 5963726977


with sq.connect('Support.db') as con:
    query = 'select * from employees'
    res = con.execute(query)

for i in res:
    print(i)
