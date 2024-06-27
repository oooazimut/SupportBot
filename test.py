a = ((1, '3'), (2, '4'), (5, '6'))
x = '1'

b = next((i[0] for i in a if i[1] == x), None)

print(b)
