import pyinputplus as pyip


class InvItem:
    def __init__(self, handler, code, name, inventory):
        self.handler = handler
        self.code = code
        self.name = name
        self.inventory = inventory

    def update_stock(self, stock):
        self.inventory = stock

    def add_quantity(self, quan):
        self.inventory += quan

    def subtract_quantity(self, quan):
        if quan > self.inventory:
            print("입력한 수량보다 재고가 부족하여 명령을 실행할 수 없습니다")
            return
        self.inventory -= quan


