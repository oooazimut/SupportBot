from db import db 

q = 'alter table tasks add column summary text'
db.post_query(q)
