import sqlite3

from db.service import task_service

task_1 = task_service.get_task(869)
task_2 = task_service.get_task(875)

for i in task_1, task_2:
    for key, value in i.items():
        print(key, value)
    print()

res_id_for_875 = task_1["resultid"].split(",")[-1]
res_id_for_869 = task_2["resultid"].split(",")[-1]


# print(res_id_for_869)
# print(res_id_for_875)

with sqlite3.connect("Support.db") as con:
    query = """
    UPDATE tasks
       SET 
        resultid = CASE
            WHEN taskid = 869 THEN ?
            WHEN taskid = 875 THEN ?
             END,
        media_type = CASE 
            WHEN taskid = 875 THEN NULL 
            ELSE media_type 
            END,
        media_id = CASE 
            WHEN taskid = 875 THEN NULL 
            ELSE media_id 
            END
     WHERE taskid IN (869, 875)
    """
    con.execute(query, [res_id_for_869, res_id_for_875])

task_1 = task_service.get_task(869)
task_2 = task_service.get_task(875)

for i in task_1, task_2:
    for key, value in i.items():
        print(key, value)
    print()
