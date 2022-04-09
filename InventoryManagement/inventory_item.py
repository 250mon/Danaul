import pyinputplus as pyip


class InvItem:
    def __init__(self, handler, code, name):
        handler = handler
        code = code
        name = name
        stock = 0

    def update_stock(self, stock):
        self.stock = stock

    def add_quantity(self, quan):
        self.stock += quan

    def subtract_quantity(self, quan):
        if quan > self.stock:
            print("입력한 수량보다 재고가 부족하여 명령을 실행할 수 없습니다")
            return
        self.stock -= quan


