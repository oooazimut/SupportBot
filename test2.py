from db import db

db.post_query('alter table tasks add column client info text')