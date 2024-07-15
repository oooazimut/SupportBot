from db import db

q1 = 'alter table tasks add column act integer'
q2 = 'alter table tasks add column actid text'
q3 = 'alter table tasks add column acttype text'
q4 = 'alter table tasks add column agreement text'


for q in (q1, q2, q3, q4):
    db.post_query(q)
