# from config import ROBERT_ID
from config import ROBERT_ID
from db.service import customer_service, employee_service


users = employee_service.get_all()
[print(user['username'], user['userid'], user['position']) for user in users]

# employee_service.change_position(1068167772)
