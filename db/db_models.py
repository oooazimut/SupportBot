from abc import ABC, abstractmethod
import sqlite3 as sq

from db.db_config import CREATE_DB_SCRIPT


class DataBase(ABC):
    @abstractmethod
    def select_query(self, query, params):
        pass

    @abstractmethod
    def post_query(self, query, params):
        pass


class SqLiteDataBase(DataBase):
    def __init__(self, name):
        self.name = name
        with sq.connect(self.name) as con:
            con.executescript(CREATE_DB_SCRIPT)

    def select_query(self, query, params=None) -> list[dict]:
        if params is None:
            params = []
        with sq.connect(self.name, detect_types=sq.PARSE_COLNAMES | sq.PARSE_DECLTYPES) as con:
            con.row_factory = sq.Row
            temp = con.execute(query, params).fetchall()
            result = []
            if temp:
                for i in temp:
                    item = dict(zip(i.keys(), tuple(i)))
                    result.append(item)
            if len(result) == 1:
                return result[0]
            return result

    def post_query(self, query: str, params=None) -> None:
        if params is None:
            params = []
        with sq.connect(self.name, detect_types=sq.PARSE_COLNAMES | sq.PARSE_DECLTYPES) as con:
            con.execute(query, params)
            con.commit()
