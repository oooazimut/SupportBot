import sqlite3 as sq


def query_performer(query):
    with sq.connect('Support.db') as con:
        con.row_factory = sq.Row
        return con.execute(query).fetchall()


q = 'select * from entities'
objects: list[sq.Row] = query_performer(q)
for row in objects:
    print(row['ent_id'], row['name'])