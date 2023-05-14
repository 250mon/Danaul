from items import Item, Sku, Transaction


class Lab:
    def __init__(self):
        self.items = []
        self.skus = []
        self.transactions = []

    def get_items(self):
        return self.items

    def add_item(self, item: Item):
        self.items.append(item)

    def get_skus(self):
        return self.skus

    def add_sku(self, sku: Sku):
        self.skus.append(sku)

    def get_transactions(self):
        return self.transactions

    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)

