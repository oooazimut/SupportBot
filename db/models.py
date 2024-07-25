import sqlite3 as sq
from abc import ABC, abstractmethod


class DataBase(ABC):
    @abstractmethod
    def select_query(self, query, params)-> list:
        pass

    @abstractmethod
    def post_query(self, query, params):
        pass


class SqLiteDataBase(DataBase):
    def __init__(self, name, script):
        self.name = name
        with sq.connect(self.name) as con:
            con.executescript(script)

    @staticmethod
    def custom_lower(some_str: str):
        return some_str.lower()

    def select_query(self, query, params=None) -> list[dict]:
        if params is None:
            params = []
        # with sq.connect(self.name, detect_types=sq.PARSE_COLNAMES | sq.PARSE_DECLTYPES) as con:
        with sq.connect(self.name) as con:
            con.create_function('my_lower', 1, self.custom_lower)
            con.row_factory = sq.Row
            temp = con.execute(query, params).fetchall()
            result = []
            if temp:
                for i in temp:
                    item = dict(zip(i.keys(), tuple(i)))
                    result.append(item)
            return result

    def post_query(self, query: str, params=None) -> None:
        if params is None:
            params = []
        with sq.connect(self.name, detect_types=sq.PARSE_COLNAMES | sq.PARSE_DECLTYPES) as con:
            con.row_factory = sq.Row
            data = con.execute(query, params).fetchall()
            if data:
                data = data[0]
            con.commit()
        return data
