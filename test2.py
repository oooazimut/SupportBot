import asyncio
from datetime import datetime, timedelta
from db.service import JournalService

from jobs import two_reports


asyncio.run(two_reports())

