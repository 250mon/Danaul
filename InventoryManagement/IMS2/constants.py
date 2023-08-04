from enum import Enum
from functools import total_ordering

DB_SETTING_FILE = 'db_settings'
ADMIN_GROUP = ['admin', 'jye']


@total_ordering
class EditLevel(Enum):
    UserModifiable = 0
    AdminModifiable = 2
    Creatable = 3
    NotEditable = 5

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
