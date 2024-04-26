import sqlite3 as sq

MY_ID = 5963726977

with sq.connect('Support.db') as con:
    script = '''
    BEGIN TRANSACTION;
    alter table jobs
    add column dttm timestamp;
    COMMIT;
    '''
    con.executescript(script)
