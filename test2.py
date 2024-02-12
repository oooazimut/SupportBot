from db import db

db.post_query('update employees set status = "worker"')