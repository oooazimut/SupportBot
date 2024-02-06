import sqlite3 as sq
from sqlite3 import Connection


def db_connector(func, db='Support.db'):
    def wrapper(*args, **kwargs):
        with sq.connect(db, detect_types=sq.PARSE_COLNAMES | sq.PARSE_DECLTYPES) as con:
            con.row_factory = sq.Row
            return func(con, *args, **kwargs)

    return wrapper


@db_connector
def create_db(con: Connection):
    tables = '''
    BEGIN TRANSACTION;
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        username TEXT,
        status TEXT
        );
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        name TEXT,
        phone INTEGER
        );
    CREATE TABLE IF NOT EXISTS entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
        );
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone INTEGER,
        title TEXT,
        description TEXT,
        status TEXT,
        priority TEXT,
        entity INTEGER,
        FOREIGN KEY (entity) REFERENCES entities (id)
        ); 
    COMMIT; 
    '''
    con.executescript(tables)
