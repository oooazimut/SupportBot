from db import db

MY_ID = 5963726977

db.post_query('update tasks set status = "назначено", entity = 6, slave = ?', [MY_ID])