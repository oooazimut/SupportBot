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
    query = """
    SELECT *
      FROM customers
     WHERE id = ?
    """
    return con.execute(query, [cust_id]).fetchone()
