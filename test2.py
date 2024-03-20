from db.service import EntityService

data = EntityService.get_entities_by_substr('4')
if data:
    for i in data:
        print(i)
