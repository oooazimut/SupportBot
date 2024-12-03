from db.service import customer_service


users = customer_service.get_all()

print(users)

customer_service.update(6392799889, name='Дракон', object=80)

users = customer_service.get_all()
print(users)
