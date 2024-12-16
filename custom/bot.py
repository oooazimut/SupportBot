from aiogram import Bot


class MyBot(Bot):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, *args, **kwargs):
        if not hasattr(self, "initialized"):
            super().__init__(*args, **kwargs)
            self.initialized = True

    @classmethod
    def get_instance(cls):
        return cls._instance
