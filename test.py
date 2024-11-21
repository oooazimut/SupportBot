import sqlite3


with sqlite3.connect('Support.db') as con:
    con.execute('delete from employees where userid = 6392799889')
    con.commit()
