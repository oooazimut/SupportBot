from sqlite3 import Connection

from db.tools import connector


@connector
def new_customer(con: Connection, **kwargs):
    query = """
    INSERT INTO customers (id, name, phone)
         VALUES (:id, :name, :phone)
    """
    con.execute(query, kwargs)
    con.commit()


@connector
def get_customer(con: Connection, cust_id):
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
def get_customers(con: Connection):
    return con.execute("SELECT * FROM customers").fetchall()


@connector
def update(con: Connection, userid: str | int, **kwargs):
    """update name, phone, object"""
    adds = []
    for item in kwargs:
        adds.append(f"{item} = :{item}")
    kwargs.update(userid=userid)
    sub_query = ", ".join(adds)
    query = f"UPDATE customers SET {sub_query} WHERE id = :userid"
    con.execute(query, kwargs)
    con.commit()
