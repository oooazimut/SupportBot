from db import db
from  db import empl_service


MY_ID = 5963726977

empl_service.save_employee(MY_ID, 'Марат', 'operator')


def is_existing(argument):
    if argument:
        return True