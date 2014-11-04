
from django.db.backends.sqlite3.base import *

class DatabaseOperations(DatabaseOperations):
    compiler_module = __package__ + '.compiler'

class DatabaseWrapper(DatabaseWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ops = DatabaseOperations(self)
