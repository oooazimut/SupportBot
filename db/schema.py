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
        simple_report TEXT,
        recom_time INTEGER,
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
    CREATE TABLE IF NOT EXISTS cars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model TEXT,
        state_number TEXT
        );
    CREATE TABLE IF NOT EXISTS cars_in_use (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dttm timestamp,
        car INTEGER,
        user INTEGER,
        FOREIGN KEY (car) REFERENCES cars (id),
        FOREIGN KEY (user) REFERENCES employees (userid)
        );
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        name TEXT,
        phone TEXT,
        object INTEGER,
        FOREIGN KEY (object) REFERENCES entities (ent_id)
        );
    COMMIT; 
    """
