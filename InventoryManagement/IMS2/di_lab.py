import os
import asyncio
from typing import List
from datetime import date
from di_db import InventoryDb
import pandas as pd
from di_logger import Logs, logging
from constants import MAX_TRANSACTION_COUNT
from singleton import Singleton


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)


class Lab(metaclass=Singleton):
    def __init__(self, di_db: InventoryDb):
        self.di_db = di_db
        self.di_db_util = self.di_db.db_util
        self.max_transaction_count = MAX_TRANSACTION_COUNT

        self.items = {}
        self.skus = {}
        self.transactions = {}

        self.table_df = {
            'category': None,
            'users': None,
            'transaction_type': None,
            'items': None,
            'skus': None,
            'transactions': None
        }

        self.table_column_names = {
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
            # getting column names
            get_data = [self._get_col_names_from_db(table) for table
                        in self.table_column_names.keys()]
            col_names: List = await asyncio.gather(*get_data)
            for table in reversed(self.table_column_names.keys()):
                self.table_column_names[table] = col_names.pop()

            # getting dfs
            get_data = [self._get_df_from_db(table) for table
                        in self.table_df.keys()]
            data_dfs: List = await asyncio.gather(*get_data)
            for df in data_dfs:
                logger.debug(f"Retrieved DB data \n{df}")
            for table in reversed(self.table_df.keys()):
                self.table_df[table] = data_dfs.pop()

            # make reference series
            self.make_ref_series()

        self.bool_initialized = True
        return self

    def __await__(self):
        return self.async_init().__await__()

    def set_max_transaction_count(self, count: int):
        if count > 0:
            self.max_transaction_count = count
        else:
            logger.warn(f""
                        f"count({count}) is not a positive integer")

    async def _get_col_names_from_db(self, table: str, **kwargs) -> List:
        logger.debug(f"{table}")
        query = f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = $1"
        db_results = await self.di_db_util.select_query(query, [table])
        logger.debug(f"{db_results}")
        col_name_list = self._db_to_list(db_results)
        return col_name_list

    def _db_to_list(self, db_records):
        # [{'col1': v11, 'col2': v12}, {'col1': v21, 'col2': v22}, ...]
        col_name_list = [record['column_name'] for record in db_records]
        return col_name_list

    async def _get_df_from_db(self, table: str, **kwargs) -> pd.DataFrame:
        logger.debug(f"{table}")
        if table == "transactions":
            sku_id = kwargs.get('sku_id', None)
            beg_ts = kwargs.get('beg_timestamp', '')
            end_ts = kwargs.get('end_timestamp', '')
            if sku_id is None:
                query = f"SELECT * FROM transactions order by tr_id desc limit " \
                        f"{self.max_transaction_count}"
            else:
                if beg_ts != '' and end_ts != '':
                    query = f"SELECT * FROM transactions where sku_id = {sku_id} " \
                            f"and tr_timestamp >= '{beg_ts}' and tr_timestamp <= '{end_ts}' " \
                            f"order by tr_id desc limit {self.max_transaction_count}"
                else:
                    # beg_ts == '' or end_ts == '':
                    query = f"SELECT * FROM transactions where sku_id = {sku_id} " \
                            f"order by tr_id desc limit {self.max_transaction_count}"
        else:
            query = f"SELECT * FROM {table}"
        logger.debug(f"{query}")

        db_results = await self.di_db_util.select_query(query)
        logger.debug(f"{db_results[:2]}")
        if db_results is None:
            return pd.DataFrame()
        df = self._db_to_df(db_results)
        return df

    def _db_to_df(self, db_records):
        # [{'col1': v11, 'col2': v12}, {'col1': v21, 'col2': v22}, ...]
        list_of_dict = [dict(record) for record in db_records]
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
        self.tr_type_s = make_series('transaction_type', True)
        self.tr_type_id_s = make_series('transaction_type', False)
        self.user_name_s = make_series('users', True)
        self.user_id_s = make_series('users', False)

    async def update_lab_df_from_db(self, table: str, **kwargs):
        logger.debug(f"table {table}")
        self.table_df[table] = await self._get_df_from_db(table, **kwargs)

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
    # print(lab.skus_df)
    #
    # sku_idx_df = lab.skus_df.set_index('sku_id')
    #
    # lab.trs_df['item_name'] = lab.trs_df['sku_id'].map(sku_idx_df['item_name'])
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
    danaul_db = InventoryDb('di_config')
    lab = Lab(danaul_db)
    asyncio.run(main(lab))
