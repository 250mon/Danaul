from datetime import date
import pyinputplus as pyip
from inventory_db import InventoryDB
from inventory_item import InvItem


class ItemsHandler:
    def __init__(self, inv_db):
        # items_dict: key:item_code, value:inventory item instance
        self.inv_db = inv_db
        self._fetch_from_db()

    def update_items_dict(self):
        """
        Update items_dict with the current db
        :return:
        """
        self._fetch_from_db()

    def _fetch_from_db(self):
        """
        Query the last transaction for each item
        and put them in the items_dict
        DB schema:
                 id integer PRIMARY KEY,
                 item_code text NOT NULL,
                 item_name text NOT NULL,
                 category text NOT NULL,
                 quantity integer NOT NULL,
                 inventory integer NOT NULL,
                 date text NOT NULL,
        :return:
        """
        self.items_dict = {}
        rows = self.inv_db.select_all_last_transactions()
        for row in rows:
            item_code = row[1]
            item_name = row[2]
            inventory = row[5]
            # make an instance of item
            item = InvItem(self, item_code, item_name, inventory)
            # append item to the items_dict
            self.items_dict[item_code] = item

    def _insert_to_db(self, code, name, cat, quan, inv):
        # insert a transaction to the db
        transaction = (code, name, cat, quan, inv, date.today().isoformat())
        self.inv_db.create_transaction(transaction)

    def create_new_item(self):
        print("========== 새로운 품목 생성 ===========")
        code = pyip.inputStr("코드 입력 (Press Enter to Exit): ")
        if code == '':
            return
        elif code in self.items_dict.keys():
            print(f"이미 존재 하는 코드({code})이며 새로 아이템을 생성할 수 없습니다.")
            return

        name = pyip.inputStr("이름 입력: ")
        inventory = pyip.inputInt("입고 수량 입력: ")

        if inventory < 1:
            print("수량은 0 보다 큰 수를 입력 해야 합니다.")
            return

        # insert it to the db
        self._insert_to_db(code, name, 'inbound', inventory, inventory)
        self.update_items_dict()

    # '': exit or default  '99': exit
    # return: a tuple containing validity and code (True or False, code)
    def _check_code(self, code):
        if code == '' or code == '99' or code in self.items_dict.keys():
            return True, code
        else:
            return False, code
            # raise Exception(f"존재하 않는 코드({code})입니다.")

    def create_transaction(self):
        print("========== 입출고 거래 생성 ===========")
        valid, code = pyip.inputCustom(self._check_code, "코드 입력 (Press Enter to Exit): ", blank=True)
        if not valid or code == '':
            return

        # print current inventory
        self.display_inventory(code)

        item = self.items_dict[code]
        item_name = item.get_name()
        inventory = item.get_inventory()

        cat = pyip.inputMenu(['1', '2'], "거래 분류(1:입고, 2:출고):\n")
        if cat == '1':
            sign = 1
            category = 'inbound'
        elif cat == '2':
            sign = -1
            category = 'outbound'
        else:
            raise Exception("No such category")

        quan = pyip.inputInt("수량 입력: ")
        quan *= sign
        if (inventory + quan) < 0:
            print("재고 수량을 초과 하여 출고 하려고 합니다. 수량을 다시 확인 하세요.")
            return

        new_inventory = item.update_inventory(quan)

        # insert it the db
        self._insert_to_db(code, item_name, category, quan, new_inventory)
        # print new inventory
        print("\n변경후 ...")
        self.display_inventory(code)

    # when item is sold, db is updated by this transaction
    def create_inout_transaction(self, code, count=1, category="outbound"):
        # print current inventory
        valid, _ = self._check_code(code)
        if not valid:
            return

        self.display_inventory(code)
        item = self.items_dict[code]
        item_name = item.get_name()
        inventory = item.get_inventory()
        if inventory == 0:
            print("재고가 없어 출고할 수 없습니다.")
            return

        if category == "outbound":
            quan = count * -1
        elif category == "inbound":
            quan = count
        else:
            print("Wrong category")
            return

        new_inventory = item.update_inventory(quan)

        # insert it the db
        self._insert_to_db(code, item_name, category, quan, new_inventory)
        # print new inventory
        print("\n변경후 ...")
        self.display_inventory(code)

    # interactive mode for outbound of a single unit of item
    def unit_outbound(self):
        while(1):
            print("========== 출고 모드 ===========")
            valid, code = pyip.inputCustom(self._check_code, "코드 입력 (Exit: 99): ", blank=True)
            if not valid or code == '99':
                return
            elif code != '':
                self.create_inout_transaction(code)
            print("\n\n")

    # outbound of a list of items represented by code_list and quan_list
    def multi_inout(self, code_list, quan_list, category="outbound"):
        for c, q in zip(code_list, quan_list):
            valid, _ = self._check_code(c)
            if valid:
                self.create_inout_transaction(c, q, category)

    def display_items_db(self, code=None):
        if code is None:
            valid, code = pyip.inputCustom(self._check_code, "코드 입력 (전체보기 Enter): ", blank=True)

        # if code is not valid, return
        if not valid:
            print(f"Code({code} not found")
            return

        header = 'Index Code, Name, Category, Transaction_Quantity, Inventory, Date'
        print(header)

        if code == '' or code == '99':
            rows = self.inv_db.select_all_transactions()
        else:
            rows = self.inv_db.select_transaction_by_code(code)

        for row in rows:
            print(row)

    def display_inventory(self, code=None):
        if code is None:
            valid, code = pyip.inputCustom(self._check_code, "코드 입력 (전체보기 Enter): ", blank=True)
            # if code is not valid, return
            if not valid:
                print(f"Code({code} not found")
                return

        codestr = 'Code'.ljust(10)
        namestr = 'Name'.ljust(20)
        invstr = 'Inventory'.rjust(10)
        header = codestr + namestr + invstr
        print(header)

        if code == '' or code == '99':
            for item in reversed(self.items_dict.values()):
                print(item)
        else:
            print(self.items_dict[code])

    def update_db_transaction(self):
        print("========== DB 수정 ===========")
        sure = pyip.inputMenu(['y', 'n'], 'Are you sure? \n')
        if sure == 'n':
            return

        valid, code = pyip.inputCustom(self._check_code, "코드 입력 (Exit: 99): ")
        if not valid or code == '99':
            return

        self.display_items_db(code)
        index = pyip.inputInt('Index: ')
        category = pyip.inputMenu(['inbound', 'outbound'], 'Category: \n')
        quan = pyip.inputInt('Quantity: ')
        if quan == 0:
            print('Quantity must not be 0... Update failed.')
            return
        inventory = pyip.inputInt('Inventory: ')
        if inventory < 0:
            print('Inventory must be greater than 0... Update failed.')
            return

        try:
            trans = (category, quan, inventory, index)
            self.inv_db.update_transaction(trans)
            self.update_items_dict()
        except:
            print("An exception occured")

        self.display_items_db(code)

    def delete_db_transaction(self):
        print("========== DB 삭제 ===========")
        code = pyip.inputStr("코드 입력 (Exit: 99): ")
        if code == '99':
            return
        elif code == '024659898':
            self.inv_db.delete_all_transactions()
            self.update_items_dict()
            # display the db contents of all items
            self.display_items_db('99')
        elif code in self.items_dict.keys():
            self.display_items_db(code)
            index = pyip.inputInt('Index: ')
            try:
                self.inv_db.delete_transaction(index)
                self.update_items_dict()
                # display the db contents of the code
                self.display_items_db(code)
            except:
                print("An exception occured")
        else:
            return




if __name__ == '__main__':
    inv_db = InventoryDB('test_inventory.db')
    items_handler = ItemsHandler(inv_db)

    while(1):
        print("0. 출고 모드")
        print("1. 새로운 코드 만들기")
        print("2. 입고 또는 출고 입력")
        print("3. 현 재고 현황")
        print("4. 입출고 리스트")
        print("5. DB 수정")
        print("99. 종료\n")
        user_input = pyip.inputInt("번호 입력: ")
        if user_input == 0:
            items_handler.unit_outbound()
        elif user_input == 1:
            items_handler.create_new_item()
        elif user_input == 2:
            items_handler.create_transaction()
        elif user_input == 3:
            items_handler.display_inventory()
        elif user_input == 4:
            items_handler.display_items_db()
        elif user_input == 5:
            items_handler.update_db_transaction()
        elif user_input == 88:
            items_handler.delete_db_transaction()
        elif user_input == 99:
            break
        else:
            print("번호를 잘못 입력하였습니다.")
        print("\n\n")