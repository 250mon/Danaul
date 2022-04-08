from datetime import date
import pyinputplus as pyip
from inventory_db import InventoryDB


class ItemsHandler:
    def __init__(self, inv_db):
        items_list = None
        inv_db = inv_db

    def create_item(self):
        code = pyip.inputStr()
        name = pyip.inputStr()
        item = (code, name)

        self.inv_db.create_item(item)

    def create_transaction(self):
        code = pyip.inputStr()
        self.inv_db.select_transaction_by_code(code)

        cat = pyip.inputMenu(['buy', 'sell'])
        quantity = pyip.inputInt()


if __name__ == '__main__':
    inv_db = InventoryDB('test_inventory.db')
    items_handler = ItemsHandler(inv_db)