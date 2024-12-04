from datetime import datetime
from sqlite3 import Connection

from db.tools import connector


@connector
def new(con: Connection, **kwargs):
    query = """
    INSERT INTO cars (model, state_number) 
         VALUES (:model, :state_number)
    """
    con.execute(query, kwargs)
    con.commit()


@connector
def update(con: Connection, **kwargs):
    car_id = kwargs.pop("id")
    sub_query = ", ".join(f"{item} = :{item}" for item in kwargs)
    kwargs.update(id=car_id)
    query = f"UPDATE cars SET {sub_query} WHERE id = :id"
    con.execute(query, kwargs)
    con.commit()


@connector
def delete(con: Connection, car_id):
    query = """
    DELETE FROM cars 
          WHERE id = ?
    """
    con.execute(query, [car_id])
    con.commit()


@connector
def get_one(con: Connection, car_id):
    query = """
    SELECT * 
      FROM cars 
     WHERE id = ?
    """
    return con.execute(query, [car_id]).fetchone()


@connector
def get_all(con: Connection):
    query = """
    SELECT *
      FROM cars
    """
    return con.execute(query).fetchall()


@connector
def pin_car(con: Connection, car_id, user_id):
    curr_dttm = datetime.now().replace(microsecond=0)
    query = """
    INSERT INTO cars_in_use (dttm, car, user) 
         VALUES (?, ?, ?)
    """
    con.execute(query, [curr_dttm, car_id, user_id])


@connector
def get_pinned_cars(con: Connection, **kwargs):
    # inner_query = '''
    # SELECT ciu.dttm AS dttm, c.model AS model, c.state_number AS state_number,
    #     ROW_NUMBER() OVER(PARTITION BY c.model, c.state_number ORDER BY ciu.dttm) AS rn
    #             FROM cars_in_use AS ciu
    #        LEFT JOIN cars AS c
    #               ON ciu.car = c.id

    # '''
    # adds = list()
    # if kwargs:
    #     for key in ("user", "car"):
    #         if kwargs.get(key):
    #             adds.append(f"ciu.{key} = :{key}")
    #     if kwargs.get("dttm"):
    #         adds.append("DATE(ciu.dttm) = :dttm")
    #     inner_query += " WHERE " + " AND ".join(adds)
    # query =f"""
    #       WITH RankedCars AS ({inner_query})
    #     SELECT dttm, model, state_number
    #       FROM RankedCars
    #      WHERE rn = 1
    #     """

    query = """
       SELECT ciu.dttm AS dttm, c.model AS model, c.state_number AS state_number
         FROM cars_in_use AS ciu
    LEFT JOIN cars AS c 
           ON ciu.car = c.id
    """
    adds = list()
    if kwargs:
        for key in ("user", "car"):
            if kwargs.get(key):
                adds.append(f"ciu.{key} = :{key}")
        if kwargs.get("dttm"):
            adds.append("DATE(ciu.dttm) = :dttm")
        query += " WHERE " + " AND ".join(adds)

    return con.execute(query, kwargs).fetchall()
