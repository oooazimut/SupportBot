from ..models import SqLiteDataBase as SqDB

def save_employee(userid: int, username: str, position: str):
    params = [userid, username, position]
    SqDB.post_query(
        "INSERT INTO employees(userid, username, position) VALUES (?, ?, ?) RETURNING *",
        params,
    )


def get_employee(userid) -> dict:
    employee = SqDB.select_query(
        "SELECT * FROM employees WHERE userid = ?", [userid]
    )
    if employee:
        return employee[0]
    else:
        return {}


def get_employees():
    data = SqDB.select_query("SELECT * FROM employees", params=None)
    return data


def get_employees_by_position(position):
    data = SqDB.select_query(
        "SELECT * FROM employees WHERE position = ?", [position]
    )
    return data

