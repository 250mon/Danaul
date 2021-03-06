from inventory_db import InventoryDB
from items_handler import ItemsHandler
import pyinputplus as pyip
import pandas as pd
from datetime import date
import os

class InvSystem:
    def __init__(self, db_file):
        self.inv_db = InventoryDB(db_file)
        self.items_handler = None

    def _export_xl(self):
        """
        Export data from the db to xl_file
        :return:
        """
        print("1. 현 재고 현황")
        print("2. 모든 거래 기록")
        print("99. Exit\n")
        user_input = pyip.inputInt('번호 입력: ')
        if user_input == 1:
            file_name = date.today().isoformat() + '_inventory.xlsx'
            self._write_inventory_to_xl(file_name)
        elif user_input == 2:
            file_name = date.today().isoformat() + '_all_transactions.xlsx'
            self._write_transactions_to_xl(file_name)
        elif user_input == 99:
            return
        else:
            return

    def _write_inventory_to_xl(self, file_path):
        items_df = pd.read_sql('SELECT item_code, item_name, inventory FROM transactions' \
                               ' WHERE id in (SELECT MAX(id) FROM transactions GROUP BY item_code)' \
                               ' ORDER BY id DESC',
                                self.inv_db.connection)
        items_df.to_excel(file_path, index=False)

    def _write_transactions_to_xl(self, file_path):
        items_df = pd.read_sql('SELECT * FROM transactions',
                               self.inv_db.connection)
        items_df.to_excel(file_path, index=False)

    def _import_xl(self):
        """
        Import data from xl_file to initialize the db
        :param xl_file:
        :return:
        """
        file_path = pyip.inputFilepath('파일 경로를 입력(Exit: 99): ')
        if file_path == '99':
            return
        elif os.path.isfile(file_path):
            self._read_xl(file_path)
        else:
            print('Error: File path not exists')
            return

    def _read_xl(self, file_path):
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
            self.items_handler.update_items_dict()
            self.items_handler.display_inventory('99')
            print('읽어오기 성공')
        except:
            print('File path is not an appropriate excel file')

    def initialize_items_handler(self):
        self.items_handler = ItemsHandler(self.inv_db)

    def _sub_menu(self):
        while True:
            print("1. 엑셀 파일 읽어 오기")
            print("2. 엑셀 파일 내보 내기")
            print("3. 새로운 코드 만들기")
            print("4. 입고 또는 출고 입력")
            print("5. DB 삭제")
            print("6. DB 수정")
            print("99. 종료\n")

            user_input = pyip.inputInt("번호 입력: ")
            if user_input == 1:
                self._import_xl()
            elif user_input == 2:
                self._export_xl()
            elif user_input == 3:
                self.items_handler.create_new_item()
            elif user_input == 4:
                self.items_handler.create_transaction()
            elif user_input == 5:
                self.items_handler.delete_db_transaction()
            elif user_input == 6:
                self.items_handler.update_db_transaction()
            elif user_input == 99:
                break
            else:
                print("번호를 잘 못 입력 했습니다.")
            print("\n\n")

    def run(self):
        while True:
            print("1. 출고 모드")
            print("2. 현 재고 현황")
            print("3. 입출고 리스트")
            print("4. 관리자 메뉴")
            print("99. 종료\n")

            user_input = pyip.inputInt("번호 입력: ")
            if user_input == 1:
                self.items_handler.single_sell_mode()
            elif user_input == 2:
                self.items_handler.display_inventory()
            elif user_input == 3:
                self.items_handler.display_items_db()
            elif user_input == 4:
                self._sub_menu()
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
