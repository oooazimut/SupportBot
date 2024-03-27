from db.service import EntityService

a = 'None'
print(type(eval(a)))
b = 'a'
c = a or b

print(type(eval(b)))