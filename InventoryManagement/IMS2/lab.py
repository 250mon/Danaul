import asyncio
from asyncpg import Record
from typing import List, Tuple, Dict
from datetime import date
from data_classes import Item, Sku, Transaction
from di_db import InventoryDb
from di_db import logging
from di_logger import Logs


sku_query = """
    SELECT
        s.sku_id, s.sku_valid, s.bit_code, s.sku_qty, s.min_qty,
        s.item_id, s.item_size_id, s.item_side_id, s.expiration_date,
        i.item_name, isz.item_size, isd.item_side
    FROM skus AS s
    JOIN items AS i USING(item_id)
    JOIN item_size AS isz USING(item_size_id)
    JOIN item_side AS isd USING(item_side_id)
"""

transaction_query = """
    SELECT 
        t.tr_id, t.user_id, t.sku_id, t.tr_type_id, t.tr_qty,
        t.before_qty, t.after_qty, t.tr_timestamp, tt.tr_type,
        i.item_name, isz.item_size, isd.item_side, u.user_name, 
    FROM transactions AS t
    JOIN skus AS s USING(sku_id)
    JOIN items AS i USING(item_id)
    JOIN transaction_type AS tt USING(tr_type_id)
    JOIN item_size AS isz USING(item_size_id)
    JOIN item_side AS isd USING(item_side_id)
    JOIN users As u USING(user_id)
"""

class Lab:
    def __init__(self, di_db: InventoryDb):
        self.di_db_util = di_db.db_util
        self.category = {}
        self.items = {}
        self.skus = {}
        self.transactions = {}

        self.logs = Logs()
        self.logger = self.logs.get_logger('lab')
        self.logger.setLevel(logging.DEBUG)

    def get_item(self, id: int):
        return self.items.get(id, None)

    def add_item(self, item: Item):
        if item.item_id not in self.items.keys():
            self.items[item.item_id] = item
        else:
            self.logger.warning(f'Lab: add_item cannot update the \
             dict because of the duplicate id {item.item_id}')

    def init_items(self):
        self.items = self.get_items_from_db()

    def get_sku(self, id: int):
        return self.skus.get(id, None)

    def add_sku(self, sku: Sku):
        if sku.sku_id not in self.skus.keys():
            self.skus[sku.sku_id] = sku
        else:
            self.logger.warning(f'Lab: add_sku cannot update the \
             dict because of the duplicate id {sku.sku_id}')

    def init_skus(self):
        self.skus = self.get_skus_from_db()

    def get_transaction(self, id: int):
        return self.transactions.get(id, None)

    def add_transaction(self, transaction: Transaction):
        if transaction.tr_id not in self.transactions.keys():
            self.transactions[transaction.tr_id] = transaction
        else:
            self.logger.warning(f'Lab: add_tr cannot update the \
             dict because of the duplicate id {transaction.tr_id}')

    def init_transactions(self):
        self.transactions = self.get_transactions_from_db()

    async def get_items_from_db(self) -> Dict[int, Item]:
        query = "SELECT * FROM items"
        results = await self.di_db_util.select_query(query)
        items = [Item(*(dict(result).values())) for result in results]
        return {item.item_id: item for item in items}

    async def get_item_from_db_by_id(self, id: int) -> Item:
        query = "SELECT * FROM items WHERE items.item_id=$1"
        results = await self.di_db_util.select_query(query, [id, ])
        return Item(*(dict(results[0]).values()))

    async def get_item_from_db_by_name(self, name: str) -> Item:
        query = "SELECT * FROM items WHERE items.item_name=$1"
        results = await self.di_db_util.select_query(query, [name, ])
        return Item(*(dict(results[0]).values()))

    async def get_skus_from_db(self) -> Dict[int, Sku]:
        query = sku_query
        results = await self.di_db_util.select_query(query)
        skus = [Sku(*(dict(result).values())) for result in results]
        return {sku.sku_id: sku for sku in skus}

    async def get_sku_from_db_by_id(self, id: int) -> Sku:
        query = "SELECT * FROM skus WHERE skus.sku_id=$1"
        results = await self.di_db_util.select_query(query, [id, ])
        return Sku(*(dict(results[0]).values()))

    async def get_sku_from_db_by_item_id(self, id: int) -> Dict[int, Sku]:
        query = "SELECT * FROM skus WHERE skus.item_id=$1"
        results = await self.di_db_util.select_query(query, [id, ])
        skus = [Sku(*(dict(result).values())) for result in results]
        return {sku.sku_id: sku for sku in skus}

    async def get_transactions_from_db(self, id: int) -> Dict[int, Transaction]:
        query = "SELECT * FROM transactions"
        results = await self.di_db_util.select_query(query)
        trs = [Transaction(*(dict(result).values())) for result in results]
        return {tr.tr_id: tr for tr in trs}

    async def get_transaction_from_db_by_id(self, id: int) -> Transaction:
        query = "SELECT * FROM transactions as t WHERE t.tr_id=$1"
        results = await self.di_db_util.select_query(query, [id, ])
        return Transaction(*(dict(results[0]).values()))

    async def get_transactions_from_db_by_sku_id(self,
                                                 id: int) -> Dict[int, Transaction]:
        query = "SELECT * FROM transactions as t WHERE t.sku_id=$1"
        results = await self.di_db_util.select_query(query, [id, ])
        trs = [Transaction(*(dict(result).values())) for result in results]
        return {tr.tr_id: tr for tr in trs}

    async def get_transactions_from_db_by_date(self,
                                               start_date: date,
                                               end_date: date) -> Dict[int, Transaction]:
        query = """ SELECT * FROM transactions as t
                        WHERE tr_timestamp::date >= $1
                        AND tr_timestamp::date <= $2 """
        args = (start_date, end_date)
        results = await self.di_db_util.select_query(query, [args, ])
        trs = [Transaction(*(dict(result).values())) for result in results]
        return {tr.tr_id: tr for tr in trs}


async def main():
    danaul_db = InventoryDb('db_settings')
    lab = Lab(danaul_db)
    # item = await lab.get_item_from_db_by_id(1)
    # print(item.item_name)
    # transaction = await lab.get_transaction_from_db_by_id(1)
    # print(transaction.tr_timestamp)
    #
    skus = await lab.get_skus_from_db()
    # skus = await lab.get_sku_from_db_by_item_id(1)
    for sku in skus.values():
        print(sku.sku_id)
    #
    # trs = await lab.get_transactions_from_db_by_sku_id(1)
    # for tr in trs.values():
    #     print(tr.tr_id)

    # s_date = date.today()
    # e_date = date.today()
    # trs = await lab.get_transactions_from_db_by_date(s_date, e_date)
    # for tr in trs.values():
    #     print(tr.tr_id)

if __name__ == '__main__':
    asyncio.run(main())
