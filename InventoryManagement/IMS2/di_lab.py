import os
import sys
import asyncio
from typing import List
from datetime import date
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
        s.sku_id, s.active, s.bit_code, s.sku_qty, s.min_qty,
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
            data_dfs: List = await asyncio.gather(*get_data)

            for df in data_dfs:
                if df.empty:
                    logger.error(f'async_init: Failed to retrieve DB data')
                    logger.error(f'async_init: {data_dfs}')
                    sys.exit(0)

            for table in reversed(self.table_df.keys()):
                self.table_df[table] = data_dfs.pop()

            # make reference series
            self.make_ref_series()

        self.bool_initialized = True
        return self

    def __await__(self):
        return self.async_init().__await__()

    async def _get_df_from_db(self, table: str) -> pd.DataFrame:
        logger.debug(f'_get_df_from_db: {table}')
        query = f"SELECT * FROM {table}"
        db_results = await self.di_db_util.select_query(query)
        logger.debug(f'_get_df_from_db: db_results: {db_results}')
        if db_results is None:
            return pd.DataFrame()
        df = self._db_to_df(db_results)
        return df

    def _db_to_df(self, results):
        # [{'col1': v11, 'col2': v12}, {'col1': v21, 'col2': v22}, ...]
        list_of_dict = [dict(result) for result in results]
        df = pd.DataFrame(list_of_dict)
        df.fillna("", inplace=True)
        return df

    def make_ref_series(self):
        def make_series(table, is_name=True):
            ref_df = self.table_df[table]
            if is_name:
                # id becomes index
                index_col = 0
            else:
                # name becomes index
                index_col = 1
            ref_df = ref_df.set_index(ref_df.columns[index_col])
            ref_s: pd.Series = ref_df.iloc[:, 0]
            return ref_s

        self.category_name_s = make_series('category', True)
        self.category_id_s = make_series('category', False)
        self.item_size_name_s = make_series('item_size', True)
        self.item_size_id_s = make_series('item_size', False)
        self.item_side_name_s = make_series('item_side', True)
        self.item_side_id_s = make_series('item_side', False)
        self.tr_type_s = make_series('transaction_type', True)
        self.tr_type_id_s = make_series('transaction_type', False)
        self.user_name_s = make_series('users', True)
        self.user_id_s = make_series('users', False)

    async def update_lab_df_from_db(self, table: str):
        logger.debug(f'update_lab_df_from_db: table {table}')
        self.table_df[table] = await self._get_df_from_db(table)

    async def insert_df(self, table: str, new_df: pd.DataFrame):
        return await self.di_db.insert_df(table, new_df)

    async def update_df(self, table: str, up_df: pd.DataFrame):
        return await self.di_db.update_df(table, up_df)

    async def delete_df(self, table: str, del_df: pd.DataFrame):
        return await self.di_db.delete_df(table, del_df)

    async def upsert_items_df(self, items_df: pd.DataFrame):
        return await self.di_db.upsert_items_df(items_df)

    async def insert_skus_df(self, skus_df: pd.DataFrame):
        return await self.di_db.insert_df('skus', skus_df)

    async def delete_skus_df(self, skus_df: pd.DataFrame):
        return await self.di_db.delete_skus_df(skus_df)

    async def insert_trs_df(self, trs_df: pd.DataFrame):
        return await self.di_db.insert_df('transactions', trs_df)

    async def delete_trs_df(self, trs_df: pd.DataFrame):
        return await self.di_db.delete_trs_df(trs_df)

    async def get_trs_df_by_date(self, start_date: date, end_date: date):
        query = """ SELECT * FROM transactions as t
                        WHERE tr_timestamp::date >= $1
                        AND tr_timestamp::date <= $2 """
        args = (start_date, end_date)
        db_results = await self.di_db_util.select_query(query, [args, ])
        df = self._db_to_df(db_results)
        return df

async def main(lab):
    cat_s = lab.categories_df.set_index('category_id')['category_name']
    isz_s = lab.item_sizes_df.set_index('item_size_id')['item_size']
    isd_s = lab.item_sides_df.set_index('item_side_id')['item_side']
    tr_type_s = lab.tr_types_df.set_index('tr_type_id')['tr_type']

    # Convert a dataframe into classes and insert them into DB
    new_items_df = pd.DataFrame([[None, True, 'n5', 2, 'lala'],
                                 [None, True, 'n6', 3, 'change']],
                                columns=['item_id', 'active', 'item_name',
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
