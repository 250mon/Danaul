from enum import Enum
from functools import total_ordering

DB_SETTING_FILE = 'db_settings'
ADMIN_GROUP = ['admin', 'jye']
MAX_TRANSACTION_COUNT = 10


class RowFlags:
    OriginalRow = 0
    NewRow = 1
    ChangedRow = 2
    DeletedRow = 4


@total_ordering
class EditLevel(Enum):
    UserModifiable = 1
    AdminModifiable = 2
    Creatable = 3
    NotEditable = 5

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
