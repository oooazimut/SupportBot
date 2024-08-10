CREATE_DB_SCRIPT = """
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
        media_type TEXT, 
        media_id TEXT,
        status TEXT,
        priority TEXT,
        entity INTEGER,
        slave INTEGER,
        result TEXT,
        resulttype TEXT,
        resultid TEXT,
        act INTEGER,
        actid TEXT,
        acttype TEXT,
        agreement TEXT,
        summary TEXT,
        FOREIGN KEY (entity) REFERENCES entities (ent_id)
        FOREIGN KEY (slave) REFERENCES employees (userid)
        ); 
    CREATE TABLE IF NOT EXISTS clones (
        taskid INTEGER
        );
    COMMIT; 
    """
