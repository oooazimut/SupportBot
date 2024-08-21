from datetime import datetime
from db.service import JournalService


journal = JournalService.get_records({"date": datetime.today().strftime("%Y-%m-%d")})
for i in journal:
    print(i.get("dttm"))
    print(i.get("record"))
