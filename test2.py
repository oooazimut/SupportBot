from db.db_config import CREATE_DB_SCRIPT
from functions.db.db_creators import SqLiteDBCreator

SqLiteDBCreator.create_db('Support.db', CREATE_DB_SCRIPT)
