from db import db

query = 'update employees set position = "worker" where userid = ?'
db.post_query(query, [6392799889])