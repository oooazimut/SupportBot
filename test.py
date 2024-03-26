import datetime

from db import task_service

MY_ID = 5963726977

# empl_service.save_employee(MY_ID, 'Марат', 'operator')

# task_service.save_task(
#     created=datetime.datetime.now(),
#     creator=MY_ID,
#     phone=89423423,
#     title='title',
#     description='description',
#     status='открыто',
#     priority='',
#     entity=18,
#     media_id=None,
#     media_type=None,
#     slave=None
# )

task = task_service.get_task(1)
print(task)