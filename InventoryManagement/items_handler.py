from datetime import date
import pyinputplus as pyip
from inventory_db import InventoryDB
from inventory_item import InvItem


class ItemsHandler:
    def __init__(self, inv_db):
        items_dict = {}
        inv_db = inv_db



    def create_item(self, code, name):
        if code in self.items_dict.items():
            print("이미 존재하는 코드이며 새로 아이템을 생성할 수 없습니다")
            return

        code = pyip.inputStr()
        name = pyip.inputStr()
        item = InvItem(self, code, name)
        self.items_dict.setdefault()

        self.inv_db.create_item((item.code, item.name))

    def find_item_by_code(self):


    def create_transaction(self):
        code = pyip.inputStr()
        self.inv_db.select_transaction_by_code(code)

        cat = pyip.inputMenu(['buy', 'sell'])
        quantity = pyip.inputInt()



if __name__ == '__main__':
    inv_db = InventoryDB('test_inventory.db')
    items_handler = ItemsHandler(inv_db)