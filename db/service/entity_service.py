from sqlite3 import Connection

from db.tools import connector


@connector
def get_all(con: Connection):
    query = "SELECT * FROM entities"
    return con.execute(query).fetchall()


@connector
def get_entities_by_substr(con: Connection, substr: str) -> list:
    query = "SELECT * FROM entities WHERE MY_LOWER(name) LIKE MY_LOWER(?)"
    return con.execute(query, [f"%{substr}%"]).fetchall()


@connector
def get_one(con: Connection, entid: str | int) -> dict | None:
    query = "SELECT * FROM entities WHERE ent_id = ?"
    return con.execute(query, [entid]).fetchone()


@connector
def get_entity_by_name(con: Connection, ent_name: str) -> dict | None:
    result = con.execute("SELECT * FROM entities WHERE name = ?", [ent_name]).fetchone()
    return result


@connector
def get_home_and_office(con: Connection) -> list:
    query = "SELECT * from entities WHERE name in ('Офис', 'Дом')"
    return con.execute(query).fetchall()
