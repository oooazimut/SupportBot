from db import db

MY_ID = 5963726977

db.post_query('delete from tasks where taskid=23')
