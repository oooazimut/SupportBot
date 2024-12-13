import sqlite3


old_to_new_statuses = {
    "открыто": "обработана оператором",
    "назначено": "назначена исполнителю",
    "закрывается": "в процессе закрытия исполнителем",
    "выполнено": "выполнена исполнителем",
    "в работе": "принята исполнителем в работу",
    "отложено": "отложено",
    "закрыто": "перемещена в архив",
    "проверка": "проверка исполнения",
    "от клиента": "в обработке",
}
with sqlite3.connect("Support.db") as con:
    for old_status, new_status in old_to_new_statuses.items():
        con.execute(
            "update tasks set status = ? where status = ?", (new_status, old_status)
        )
        con.commit()
