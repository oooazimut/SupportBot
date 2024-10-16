from ..models import SqLiteDataBase as SqDB


def get_entities_by_substr(substr):
    query = "SELECT * FROM entities WHERE MY_LOWER(name) LIKE MY_LOWER(?)"
    return SqDB.select_query(query, [f"%{substr}%"])


def get_entity(entid):
    query = "SELECT * FROM entities WHERE ent_id = ?"
    return SqDB.select_query(query, [entid])


def get_entity_by_name(ent_name):
    query = "SELECT * FROM entities WHERE name = ?"
    return SqDB.select_query(query, [ent_name])


def get_home_and_office():
    query = "SELECT * from entities WHERE name in ('Офис', 'Дом')"
    return SqDB.select_query(query)
