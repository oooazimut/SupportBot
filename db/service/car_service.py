from datetime import datetime
from sqlite3 import Connection

from db.tools import connector


@connector
def new_car(con: Connection, **kwargs):
    query = """
    INSERT INTO cars (model, state_number) 
         VALUES (:model, :state_number)
    """
    con.execute(query, kwargs)
    con.commit()


@connector
def edit_car(con: Connection, **kwargs):
    query = """
    UPDATE cars 
       SET model = :model, 
           state_number = state_number 
     WHERE id = :car_id
    """
    con.execute(query, kwargs)
    con.commit()


@connector
def del_car(con: Connection, car_id):
    query = """
    DELETE FROM cars 
          WHERE id = ?
    """
    con.execute(query, [car_id])
    con.commit()


@connector
def get_car(con: Connection, car_id):
    query = """
    SELECT * 
      FROM cars 
     WHERE id = ?
    """
    con.execute(query, [car_id]).fetchone()


@connector
def pin_car(con: Connection, car_id, user_id):
    curr_dttm = datetime.now().replace(microsecond=0)
    query = """
    INSERT INTO cars_in_use 
         VALUES (curr_dttm, car_id, user_id)
    """
    con.execute(query, [curr_dttm, car_id, user_id])
