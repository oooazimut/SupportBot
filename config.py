import logging

from functions.db.base import create_db

TOKEN = '6525353343:AAHW8JVm3wya_x52NdUXM5lAuBqZX-afgL8'

_logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

create_db()
