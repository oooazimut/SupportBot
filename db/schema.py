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
        resultid TEXT,
        act INTEGER,
        actid TEXT,
        agreement TEXT,
        FOREIGN KEY (entity) REFERENCES entities (ent_id),
        FOREIGN KEY (slave) REFERENCES employees (userid)
        ); 
    CREATE TABLE IF NOT EXISTS journal (
        recordid INTEGER PRIMARY KEY AUTOINCREMENT,
        dttm timestamp,
        employee INTEGER,
        task INTEGER,
        record TEXT,
        FOREIGN KEY (employee) REFERENCES employees (userid),
        FOREIGN KEY (task) REFERENCES tasks (taskid)
        );
    CREATE TABLE IF NOT EXISTS receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dttm timestamp,
        employee INTEGER,
        receipt TEXT,
        caption TEXT,
        FOREIGN KEY (employee) REFERENCES employees (userid)
        );
    COMMIT; 
    """
