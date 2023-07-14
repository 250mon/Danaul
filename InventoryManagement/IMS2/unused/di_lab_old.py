import os
import asyncio
from typing import Dict
from datetime import date
from IMS2.unused.data_classes import Item, Sku, Transaction
from di_db import InventoryDb
import pandas as pd
from di_logger import Logs, logging


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


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

class Lab(metaclass=Singleton):
    def __init__(self, di_db: InventoryDb):
        self.di_db = di_db
        self.di_db_util = self.di_db.db_util

        self.items = {}
        self.skus = {}
        self.transactions = {}

        self.table_df = {
            'category': None,
            'item_size': None,
            'item_side': None,
            'users': None,
            'transaction_type': None,
            'items': None,
            'skus': None,
            'transactions': None
        }

        self.bool_initialized = False
        if not self.bool_initialized:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(self.async_init())
            finally:
                loop.close()

    async def async_init(self):
        if self.bool_initialized is False:
            # get etc dfs
            get_data = [self._get_df_from_db(table) for table
                        in self.table_df.keys()]
            data = await asyncio.gather(*get_data)
            for table in reversed(self.table_df.keys()):
                self.table_df[table] = data.pop()

        self.bool_initialized = True
        return self

    def __await__(self):
        return self.async_init().__await__()

    async def _get_df_from_db(self, table: str) -> pd.DataFrame:
        logger.debug(f'_get_df_from_db: {table}')
        query = f"SELECT * FROM {table}"
        results = await self.di_db_util.select_query(query)
        # [{'col1': v11, 'col2': v12}, {'col1': v21, 'col2': v22}, ...]
        list_of_dict = [dict(result) for result in results]
        df = pd.DataFrame(list_of_dict)
        df.fillna("", inplace=True)
        logger.debug(f'\n{df}')
        return df

    async def update_lab_df_from_db(self, table: str):
        logger.debug(f'update_lab_df_from_db: table {table}')
        self.table_df[table] = await self._get_df_from_db(table)

    async def insert_items_df(self, items_df: pd.DataFrame):
        return await self.di_db.insert_items_df(items_df)

    async def upsert_items_df(self, items_df: pd.DataFrame):
        return await self.di_db.upsert_items_df(items_df)

    async def delete_items_df(self, items_df: pd.DataFrame):
        return await self.di_db.delete_items_df(items_df)

    def get_item(self, id: int):
        return self.items.get(id, None)

    def add_item(self, item: Item):
        if item.item_id not in self.items.keys():
            self.items[item.item_id] = item
        else:
            logger.warning(f'Lab: add_item cannot update the \
             dict because of the duplicate id {item.item_id}')

    def init_items(self):
        self.items = self.get_items_from_db()

    def get_sku(self, id: int):
        return self.skus.get(id, None)

    def add_sku(self, sku: Sku):
        if sku.sku_id not in self.skus.keys():
            self.skus[sku.sku_id] = sku
        else:
            logger.warning(f'Lab: add_sku cannot update the \
             dict because of the duplicate id {sku.sku_id}')

    def init_skus(self):
        self.skus = self.get_skus_from_db()

    def get_transaction(self, id: int):
        return self.transactions.get(id, None)

    def add_transaction(self, transaction: Transaction):
        if transaction.tr_id not in self.transactions.keys():
            self.transactions[transaction.tr_id] = transaction
        else:
            logger.warning(f'Lab: add_tr cannot update the \
             dict because of the duplicate id {transaction.tr_id}')

    def init_transactions(self):
        self.transactions = self.get_transactions_from_db()

    async def get_items_from_db(self) -> Dict[int, Item]:
        query = "SELECT * FROM items"
        results = await self.di_db_util.select_query(query)
        items = [Item(*(tuple(result))) for result in results]
        return {item.item_id: item for item in items}

    async def get_item_from_db_by_id(self, id: int) -> Item:
        query = "SELECT * FROM items WHERE items.item_id=$1"
        results = await self.di_db_util.select_query(query, [id, ])
        return Item(*(tuple(results[0])))

    async def get_item_from_db_by_name(self, name: str) -> Item:
        query = "SELECT * FROM items WHERE items.item_name=$1"
        results = await self.di_db_util.select_query(query, [name, ])
        return Item(*(tuple(results[0])))

    async def get_skus_from_db(self) -> Dict[int, Sku]:
        query = "SELECT * FROM skus"
        results = await self.di_db_util.select_query(query)
        # skus = [Sku(*(tuple(result))) for result in results]
        skus = [Sku(*(tuple(result))) for result in results]
        return {sku.sku_id: sku for sku in skus}

    async def get_sku_from_db_by_id(self, id: int) -> Sku:
        query = "SELECT * FROM skus WHERE skus.sku_id=$1"
        results = await self.di_db_util.select_query(query, [id, ])
        return Sku(*(tuple(results[0])))

    async def get_sku_from_db_by_item_id(self, id: int) -> Dict[int, Sku]:
        query = "SELECT * FROM skus WHERE skus.item_id=$1"
        results = await self.di_db_util.select_query(query, [id, ])
        skus = [Sku(*(tuple(result))) for result in results]
        return {sku.sku_id: sku for sku in skus}

    async def get_transactions_from_db(self, id: int) -> Dict[int, Transaction]:
        query = "SELECT * FROM transactions"
        results = await self.di_db_util.select_query(query)
        trs = [Transaction(*(tuple(result))) for result in results]
        return {tr.tr_id: tr for tr in trs}

    async def get_transaction_from_db_by_id(self, id: int) -> Transaction:
        query = "SELECT * FROM transactions as t WHERE t.tr_id=$1"
        results = await self.di_db_util.select_query(query, [id, ])
        return Transaction(*(tuple(results[0])))

    async def get_transactions_from_db_by_sku_id(self,
                                                 id: int) -> Dict[int, Transaction]:
        query = "SELECT * FROM transactions as t WHERE t.sku_id=$1"
        results = await self.di_db_util.select_query(query, [id, ])
        trs = [Transaction(*(tuple(result))) for result in results]
        return {tr.tr_id: tr for tr in trs}

    async def get_transactions_from_db_by_date(self,
                                               start_date: date,
                                               end_date: date) -> Dict[int, Transaction]:
        query = """ SELECT * FROM transactions as t
                        WHERE tr_timestamp::date >= $1
                        AND tr_timestamp::date <= $2 """
        args = (start_date, end_date)
        results = await self.di_db_util.select_query(query, [args, ])
        trs = [Transaction(*(tuple(result))) for result in results]
        return {tr.tr_id: tr for tr in trs}

async def main(lab):
    cat_s = lab.categories_df.set_index('category_id')['category_name']
    isz_s = lab.item_sizes_df.set_index('item_size_id')['item_size']
    isd_s = lab.item_sides_df.set_index('item_side_id')['item_side']
    tr_type_s = lab.tr_types_df.set_index('tr_type_id')['tr_type']

    # Convert a dataframe into classes and insert them into DB
    new_items_df = pd.DataFrame([[None, True, 'n5', 2, 'lala'],
                                 [None, True, 'n6', 3, 'change']],
                                columns=['item_id', 'item_valid', 'item_name',
                                         'category_id', 'description'])
    # await lab.di_db.insert_items_df(new_items_df)
    await lab.di_db.upsert_items_df(new_items_df)
    await lab.update_lab_df_from_db('items')

    # Get data from db
    lab.items_df['category'] = lab.items_df['category_id'].map(cat_s)
    print(lab.items_df)

    # i_s = lab.items_df.set_index('item_id')['item_name']
    #
    # lab.skus_df['item_name'] = lab.skus_df['item_id'].map(i_s)
    # lab.skus_df['item_size'] = lab.skus_df['item_size_id'].map(isz_s)
    # lab.skus_df['item_side'] = lab.skus_df['item_side_id'].map(isd_s)
    # print(lab.skus_df)
    #
    # sku_idx_df = lab.skus_df.set_index('sku_id')
    #
    # lab.trs_df['item_name'] = lab.trs_df['sku_id'].map(sku_idx_df['item_name'])
    # lab.trs_df['item_size'] = lab.trs_df['sku_id'].map(sku_idx_df['item_size'])
    # lab.trs_df['item_side'] = lab.trs_df['sku_id'].map(sku_idx_df['item_side'])
    # lab.trs_df['tr_type'] = lab.trs_df['tr_type_id'].map(tr_type_s)
    # print(lab.trs_df)

    # item = await lab.get_item_from_db_by_id(1)
    # print(item.item_name)

    # transaction = await lab.get_transaction_from_db_by_id(1)
    # print(transaction.tr_timestamp)

    # skus = await lab.get_skus_from_db()
    # skus = await lab.get_sku_from_db_by_item_id(1)
    # for sku in skus.values():
    #     print(sku.sku_id)
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
    danaul_db = InventoryDb('db_settings')
    lab = Lab(danaul_db)
    asyncio.run(main(lab))
