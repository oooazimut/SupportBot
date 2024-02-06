from sqlite3 import Connection

from functions.db.base import db_connector


@db_connector
def get_max_id(con: Connection):
    taskid = con.execute('SELECT MAX(id) FROM tasks').fetchone()[0]
    print(taskid)


get_max_id()
