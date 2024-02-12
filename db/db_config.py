DB_NAME = 'Support.db'

CREATE_DB_SCRIPT = '''
    BEGIN TRANSACTION;
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        username TEXT,
        status TEXT
        );
    CREATE TABLE IF NOT EXISTS entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
        );
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created timestamp,
        creator INTEGER,
        phone INTEGER,
        title TEXT,
        description TEXT,
        status TEXT,
        priority TEXT,
        entity INTEGER,
        slave INTEGER,
        FOREIGN KEY (entity) REFERENCES entities (id)
        FOREIGN KEY (slave) REFERENCES employees (id)
        ); 
    COMMIT; 
    '''