from inventory_db import InventoryDB
from items_handler import ItemsHandler
import pyinputplus as pyip
import pandas as pd
from datetime import date

class InvSystem:
    def __init__(self, db_file):
        self.inv_db = InventoryDB(db_file)
        self.items_handler = None

    def _import_xl(self):
        """
        Import data from xl_file to initialize the db
        :param xl_file:
        :return:
        """
        file_path = pyip.inputFilepath('파일 경로를 입력(Exit: 99): ')
        if file_path == '99':
            return
        try:
            inv_df = pd.read_excel(file_path)
            inv_df['category'] = 'buy'
            inv_df['quantity'] = inv_df['inventory']
            inv_df['date'] = date.today().isoformat()

            inv_df.to_sql('transactions',
                          self.inv_db.connection,
                          if_exists='append',
                          index=False,
                          # index_label='id',
                          dtype={
                              # "id": 'Integer',
                              "item_code": 'Text',
                              "item_name": 'Text',
                              "category": 'Text',
                              "quantity": 'Integer',
                              "inventory": 'Integer',
                              "date": 'Text'
                          })
            self.inv_db.select_all_transactions()
            print('읽어오기 성공')
        except:
            print('File path is incorrect')

    def initialize_items_handler(self):
        self.items_handler = ItemsHandler(self.inv_db)

    def _print_menu(self):
        print("0. 출고 모드")
        print("1. 새로운 코드 만들기")
        print("2. 입고 또는 출고 입력")
        print("3. 현 재고 현황")
        print("4. 입출고 리스트")
        print("5. DB 수정")
        print("7. 엑셀 파일 읽어오기")
        print("99. 종료\n")

    def run(self):
        while True:
            self._print_menu()

            user_input = pyip.inputInt("번호 입력: ")
            if user_input == 0:
                self.items_handler.single_sell_mode()
            elif user_input == 1:
                self.items_handler.create_new_item()
            elif user_input == 2:
                self.items_handler.create_transaction()
            elif user_input == 3:
                self.items_handler.display_inventory()
            elif user_input == 4:
                self.items_handler.display_items_db()
            elif user_input == 5:
                self.items_handler.update_db_transaction()
            elif user_input == 7:
                self._import_xl()
            elif user_input == 88:
                self.items_handler.delete_db()
            elif user_input == 99:
                break
            else:
                print("번호를 잘 못 입력 했습니다.")
            print("\n\n")


if __name__ == '__main__':
    db_file = 'inventory.db'
    system = InvSystem(db_file)
    system.initialize_items_handler()
    system.run()
