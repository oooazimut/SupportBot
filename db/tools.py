import sqlite3 as sq
from collections.abc import Callable
from typing import Any

from config import DB_NAME


def custom_lower(some_str: str):
    return some_str.lower()


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def connector(func: Callable):
    def wrapper(*args, **kwargs) -> Any:
        with sq.connect(
            # DB_NAME, detect_types=sq.PARSE_COLNAMES | sq.PARSE_DECLTYPES
            DB_NAME
        ) as con:
            con.row_factory = dict_factory
            con.create_function("my_lower", 1, custom_lower)
            result = func(con, *args, **kwargs)
            return result

    return wrapper


@connector
def create_db(con: sq.Connection, script) -> None:
    con.executescript(script)
