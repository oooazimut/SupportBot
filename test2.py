class MyClass:
    def __init__(self):
        self._my_private_variable = 42

    @property
    def my_private_variable(self):
        return self._my_private_variable

    @my_private_variable.setter
    def my_private_variable(self, value):
        self._my_private_variable = value

obj = MyClass()
print(obj.my_private_variable)  # Вывод: 42
obj.my_private_variable = 100
print(obj.my_private_variable)  # Вывод: 100

print(obj._my_private_variable)