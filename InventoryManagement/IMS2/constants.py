from enum import Enum
DB_SETTING_FILE = 'db_settings'
ADMIN_GROUP = ['admin', 'jye']
class EditLevel(Enum):
    Modifiable = 0
    Creatable = 1
    NotEditable = 5

