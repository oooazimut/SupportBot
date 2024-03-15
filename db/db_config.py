DB_NAME = 'Support.db'

CREATE_DB_SCRIPT = '''
    BEGIN TRANSACTION;
    CREATE TABLE IF NOT EXISTS employees (
        userid INTEGER PRIMARY KEY,
        username TEXT,
        position TEXT
        );
    CREATE TABLE IF NOT EXISTS entities (
        ent_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
        );
    CREATE TABLE IF NOT EXISTS tasks (
        taskid INTEGER PRIMARY KEY AUTOINCREMENT,
        created timestamp,
        creator INTEGER,
        phone INTEGER,
        title TEXT,
        description TEXT,
        client_info TEXT,
        media_type TEXT, 
        media_id INTEGER,
        status TEXT,
        priority TEXT,
        entity INTEGER,
        slave INTEGER,
        FOREIGN KEY (entity) REFERENCES entities (ent_id)
        FOREIGN KEY (slave) REFERENCES employees (userid)
        ); 
    COMMIT; 
    '''