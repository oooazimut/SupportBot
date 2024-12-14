# from config import ROBERT_ID
from config import ROBERT_ID
from db.service import customer_service, employee_service


# customer_service.delete(ROBERT_ID)
# employee_service.new(ROBERT_ID, 'Роберт', 'worker')

# employee_service.delete(ROBERT_ID)
# customer_service.new(id=ROBERT_ID, name="Роберт", phone="43534534")

# customer_service.update(object=44, id=ROBERT_ID)
customers = customer_service.get_all()
for customer in customers:
    [print(key, value) for key, value in customer.items()]
    print()

# customer_service.update(id=ROBERT_ID, object=24)
