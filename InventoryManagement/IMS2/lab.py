import asyncio
from asyncpg import Record
from typing import List, Tuple, Dict
from data_classes import Item, Sku, Transaction
from di_db import InventoryDB
from di_db import logging


class Lab:
    def __init__(self, db: InventoryDB):
        self.db = db
        self.category = {}
        self.items = {}
        self.skus = {}
        self.transactions = {}

    def get_item(self, id: int):
        return self.items.get(id, None)

    def add_item(self, item: Item):
        if item.item_id not in self.items.keys():
            self.items[item.item_id] = item
        else:
            logging.warning(f'Lab: add_item cannot update the \
             dict because of the duplicate id {item.item_id}')

    def init_items(self):
        self.items = self.get_items_from_db()

    def get_sku(self, id: int):
        return self.skus.get(id, None)

    def add_sku(self, sku: Sku):
        self.skus.append(sku)

    def init_skus(self):
        self.skus = self.get_skus_from_db()

    def get_transaction(self, id: int):
        return self.transactions.get(id, None)

    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)

    def init_transactions(self):
        self.transactions = self.get_transactions_from_db()

    async def get_items_from_db(self) -> Dict[int: Item]:
        query = "SELECT * FROM items"
        results = await self.db.select_query(query)
        items = [Item(*(dict(result).values())) for result in results]
        return {item.item_id: item for item in items}

    async def get_item_from_db_by_id(self, id: int) -> Item:
        query = "SELECT * FROM items WHERE items.item_id=$1"
        results = await self.db.select_query(query, [id,])
        return Item(*(dict(results[0]).values()))

    async def get_item_from_db_by_name(self, name: str) -> Item:
        query = "SELECT * FROM items WHERE items.item_name=$1"
        results = await self.db.select_query(query, [name,])
        return Item(*(dict(results[0]).values()))

    async def get_skus_from_db(self) -> Dict[int: Sku]:
        query = "SELECT * FROM skus"
        results = await self.db.select_query(query)
        skus = [Sku(*(dict(result).values())) for result in results]
        return {sku.sku_id: sku for sku in skus}

    async def get_sku_from_db_by_id(self, id: int) -> Sku:
        query = "SELECT * FROM skus WHERE skus.sku_id=$1"
        results = await self.db.select_query(query, [id, ])
        return Sku(*(dict(results[0]).values()))

    async def get_sku_from_db_by_item_id(self, id: int) -> Dict[int: Sku]:
        query = "SELECT * FROM skus WHERE skus.item_id=$1"
        results = await self.db.select_query(query, [id, ])
        skus = [Sku(*(dict(result).values())) for result in results]
        return {sku.sku_id: sku for sku in skus}

    async def get_transactions_from_db(self, id: int) -> Dict[int: Transaction]:
        query = "SELECT * FROM transactions"
        results = await self.db.select_query(query)
        trs = [Transaction(*(dict(result).values())) for result in results]
        return {tr.tr_id: tr for tr in trs}

    async def get_transaction_from_db_by_id(self, id: int) -> Transaction:
        query = "SELECT * FROM transactions as t WHERE t.tr_id=$1"
        results = await self.db.select_query(query, [id, ])
        return Transaction(*(dict(results[0]).values()))

    async def get_transaction_from_db_by_sku_id(self,
                                                id: int) -> Dict[int: Transaction]:
        query = "SELECT * FROM transactions as t WHERE t.sku_id=$1"
        results = await self.db.select_query(query, [id, ])
        trs = [Transaction(*(dict(result).values())) for result in results]
        return {tr.tr_id: tr for tr in trs}


async def main():
    danaul_db = InventoryDB('db_settings')
    lab = Lab(danaul_db)
    item = await lab.get_item_from_db_by_id(1)
    print(item.item_name)
    transaction = await lab.get_transaction_from_db_by_id(1)
    print(transaction.tr_timestamp)

    skus = await lab.get_sku_from_db_by_item_id(1)
    for sku in skus:
        print(sku.sku_id)

    trs = await lab.get_transaction_from_db_by_sku_id(1)
    for tr in trs:
        print(tr.tr_id)


if __name__ == '__main__':
    asyncio.run(main())
