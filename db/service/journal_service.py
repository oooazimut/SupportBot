from datetime import datetime
from ..models import SqLiteDataBase as SqDB


def new_record(data: dict):
    data.setdefault("dttm", datetime.now().replace(microsecond=0))
    query = "INSERT INTO journal (dttm, employee, task, record) VALUES (:dttm, :employee, :task, :record) RETURNING *"
    return SqDB.post_query(query, data)


def update_rec_dttm(dttm, recordid):
    query = "UPDATE journal set dttm = ? where recordid = ? RETURNING *"
    return SqDB.post_query(query, [dttm, recordid])


def get_records(**kwargs):
    data = kwargs
    query = """
    SELECT *
    FROM journal as j
    LEFT JOIN employees as e ON e.userid = j.employee
    LEFT JOIN tasks as t ON t.taskid= j.task
    LEFT JOIN entities as ent ON ent.ent_id =  t.entity 
    """
    adds = list()
    if data.get("userid"):
        adds.append("j.employee = :userid")
    if data.get("date"):
        adds.append("DATE(j.dttm) = :date")
    if data.get("taskid"):
        if data.get("taskid") == "null":
            adds.append("j.task IS NULL")
        else:
            adds.append("j.task = :taskid")
    if data.get("object"):
        adds.append("ent.name = :object")
    if data.get("record"):
        adds.append('ent.record LIKE "%:record%"')

    if adds:
        query = query + " WHERE " + " AND ".join(adds)

    query += " ORDER BY created DESC"
    return SqDB.select_query(query, data)


def get_last(userid) -> dict | None:
    curr_date = datetime.today().date()
    query = 'SELECT * FROM journal WHERE employee = ? AND DATE(dttm) = ? AND (record LIKE "%Приехал" OR record LIKE "%Уехал") ORDER BY dttm DESC LIMIT 1'
    res = SqDB.select_query(query, [userid, curr_date])
    return res[0] if res else None


def get_last_record(userid: str | int) -> str:
    result = get_last(userid)
    return result["record"] if result else ""


def get_last_record_id(userid) -> int:
    result = get_last(userid)
    return result["recordid"] if result else 0


def del_record(recordid):
    query = "DELETE FROM journal WHERE recordid = ? RETURNING *"
    SqDB.post_query(query, [recordid])
