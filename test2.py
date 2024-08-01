from db.models import SqLiteDataBase
from db.schema import CREATE_DB_SCRIPT


SqLiteDataBase.create(script=CREATE_DB_SCRIPT)
