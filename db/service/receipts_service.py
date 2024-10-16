from ..models import SqLiteDataBase as SqDB


def new_receipt(data: dict):
    query = "INSERT INTO receipts (dttm, employee, receipt, caption) VALUES (:dttm, :employee, :receipt, :caption) RETURNING *"
    SqDB.post_query(query, data)


def get_receipts(params={}):
    query = "SELECT * FROM receipts"
    adds = list()
    if params.get("dttm"):
        adds.append("DATE(dttm) = :dttm")
    if params.get("employee"):
        adds.append("employee = :employee")

    if adds:
        query += " WHERE " + " AND ".join(adds)

    return SqDB.select_query(query, params)
