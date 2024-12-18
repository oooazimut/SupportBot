from sqlite3 import Connection

from db.tools import connector


@connector
def new(con: Connection, **kwargs):
    """kwargs: id, name, phone"""
    query = """
    INSERT INTO customers (id, name, phone)
         VALUES (:id, :name, :phone)
    """
    con.execute(query, kwargs)
    con.commit()


@connector
def get_one(con: Connection, cust_id):
    """
    возвращает словарь с ключами id, name, phone, object
    """
    query = """
    SELECT *
      FROM customers
     WHERE id = ?
    """
    return con.execute(query, [cust_id]).fetchone()


@connector
def get_all(con: Connection):
    return con.execute("SELECT * FROM customers").fetchall()


@connector
def get_by_filters(con: Connection, **kwargs):
    """kwargs: name, phone, object"""
    sub_query = " AND ".join(f"{item} = :{item}" for item in kwargs)
    query = f"SELECT * FROM customers WHERE {sub_query}"
    return con.execute(query, kwargs).fetchall()


@connector
def update(con: Connection, **kwargs):
    """kwargs: id, name, phone, object"""
    userid = kwargs.pop("id")
    """update name, phone, object"""
    sub_query = ", ".join(f"{item} = :{item}" for item in kwargs)
    kwargs.update(userid=userid)
    query = f"UPDATE customers SET {sub_query} WHERE id = :userid"
    con.execute(query, kwargs)
    con.commit()


@connector
def delete(con: Connection, userid: str | int):
    con.execute("DELETE FROM customers WHERE id = ?", [userid])
    con.commit()
