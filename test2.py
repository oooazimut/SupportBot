from datetime import datetime

current_datetime = datetime.now().replace(microsecond=0)

print('Текущая дата и время без долей секунд:', current_datetime)