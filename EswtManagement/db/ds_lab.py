import os
import re
import asyncio
from typing import List
from datetime import date
from db.ds_db import TreatmentsDb
import pandas as pd
from common.d_logger import Logs, logging
from constants import MAX_TRANSACTION_COUNT
from common.singleton import Singleton
import db.db_schema



class Lab(metaclass=Singleton):
    logger = Logs().get_logger(os.path.basename(__file__))
    logger.setLevel(logging.DEBUG)

    def __init__(self, di_db: TreatmentsDb):
        self.di_db = di_db
        self.di_db_util = self.di_db.db_util
        self.max_transaction_count = MAX_TRANSACTION_COUNT
        self.show_inactive_treatments = False

        self.table_df = {
            'category': None,
            'users': None,
            'providers': None,
            'treatments': None,
            'skus': None,
            'sessions': None
        }
        self._set_db_column_names()

        self.bool_initialized = False
        if not self.bool_initialized:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(self.async_init())
            finally:
                loop.close()

    async def async_init(self):
        if self.bool_initialized is False:
            # getting dfs
            get_data = [self._get_df_from_db(table) for table
                        in self.table_df.keys()]
            data_dfs: List = await asyncio.gather(*get_data)
            for df in data_dfs:
                self.logger.debug(f"Retrieved DB data \n{df}")
            for table in reversed(self.table_df.keys()):
                self.table_df[table] = data_dfs.pop()

            # make reference series
            self._make_ref_series()

        self.bool_initialized = True
        return self

    def __await__(self):
        return self.async_init().__await__()

    def _set_max_transaction_count(self, count: int):
        if count > 0:
            self.max_transaction_count = count
        else:
            self.logger.warn(f""
                        f"count({count}) is not a positive integer")

    def _set_db_column_names(self):
        col_name = re.compile(r'''^\s*([a-z_]+)\s*''', re.MULTILINE)
        self.table_column_names = {}
        self.table_column_names['treatments'] = col_name.findall(db.inventory_schema.CREATE_TREATMENT_TABLE)
        self.table_column_names['skus'] = col_name.findall(db.inventory_schema.CREATE_SKU_TABLE)
        self.table_column_names['sessions'] = col_name.findall(db.inventory_schema.CREATE_TRANSACTION_TABLE)

    async def _get_df_from_db(self, table: str, **kwargs) -> pd.DataFrame:
        self.logger.debug(f"{table}")
        where_clause = ""
        if not self.show_inactive_treatments:
            if table == "treatments":
                where_clause = " WHERE active = True"
            elif table == "skus":
                where_clause = " WHERE (treatment_id IN (SELECT treatment_id FROM treatments WHERE active = True)) AND " \
                               "(active = True)"
            elif table == "sessions":
                where_clause = " WHERE treatment_id IN (SELECT treatment_id FROM skus AS s WHERE " \
                               "(s.treatment_id IN (SELECT treatment_id FROM treatments AS i WHERE i.active = True)) AND " \
                               "(s.active = True))"

        if table == "sessions":
            treatment_id = kwargs.get('treatment_id', None)
            beg_ts = kwargs.get('beg_timestamp', '')
            end_ts = kwargs.get('end_timestamp', '')
            if treatment_id is None:
                query = f"SELECT * FROM sessions {where_clause} ORDER BY session_id DESC LIMIT " \
                        f"{self.max_transaction_count}"
            else:
                if beg_ts != '' and end_ts != '':
                    query = f"SELECT * FROM sessions WHERE treatment_id = {treatment_id} " \
                            f"AND timestamp >= '{beg_ts}' AND timestamp <= '{end_ts}' " \
                            f"ORDER BY session_id DESC LIMIT {self.max_transaction_count}"
                else:
                    # beg_ts == '' or end_ts == '':
                    query = f"SELECT * FROM sessions WHERE treatment_id = {treatment_id} " \
                            f"ORDER BY session_id DESC LIMIT {self.max_transaction_count}"

            where_clause = ""

        else:
            query = f"SELECT * FROM {table}"

        query = query + where_clause
        self.logger.debug(f"{query}")

        db_results = await self.di_db_util.select_query(query)
        # logger.debug(f"{db_results[:2]}")
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

    def _make_ref_series(self):
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
        self.tr_type_s = make_series('providers', True)
        self.provider_id_s = make_series('providers', False)
        self.user_name_s = make_series('users', True)
        self.user_id_s = make_series('users', False)

    async def update_lab_df_from_db(self, table: str, **kwargs):
        self.logger.debug(f"table {table}")
        self.table_df[table] = await self._get_df_from_db(table, **kwargs)

    async def insert_df(self, table: str, new_df: pd.DataFrame):
        return await self.di_db.insert_df(table, new_df)

    async def update_df(self, table: str, up_df: pd.DataFrame):
        return await self.di_db.update_df(table, up_df)

    async def delete_df(self, table: str, del_df: pd.DataFrame):
        return await self.di_db.delete_df(table, del_df)

    async def upsert_treatments_df(self, treatments_df: pd.DataFrame):
        return await self.di_db.upsert_treatments_df(treatments_df)

    async def insert_skus_df(self, skus_df: pd.DataFrame):
        return await self.di_db.insert_df('skus', skus_df)

    async def delete_skus_df(self, skus_df: pd.DataFrame):
        return await self.di_db.delete_skus_df(skus_df)

    async def insert_trs_df(self, trs_df: pd.DataFrame):
        return await self.di_db.insert_df('sessions', trs_df)

    async def delete_trs_df(self, trs_df: pd.DataFrame):
        return await self.di_db.delete_trs_df(trs_df)

    async def get_trs_df_by_date(self, start_date: date, end_date: date):
        query = """ SELECT * FROM sessions as t
                        WHERE timestamp::date >= $1
                        AND timestamp::date <= $2 """
        args = (start_date, end_date)
        db_results = await self.di_db_util.select_query(query, [args, ])
        df = self._db_to_df(db_results)
        return df

async def main(lab):
    cat_s = lab.categories_df.set_index('category_id')['category_name']
    tr_type_s = lab.tr_types_df.set_index('provider_id')['tr_type']

    # Convert a dataframe into classes and insert them into DB
    new_treatments_df = pd.DataFrame([[None, True, 'n5', 2, 'lala'],
                                 [None, True, 'n6', 3, 'change']],
                                columns=['treatment_id', 'active', 'treatment_name',
                                         'category_id', 'description'])
    # await lab.di_db.insert_treatments_df(new_treatments_df)
    await lab.di_db.upsert_treatments_df(new_treatments_df)
    await lab.update_lab_df_from_db('treatments')

    # Get data from db
    lab.treatments_df['category'] = lab.treatments_df['category_id'].map(cat_s)
    print(lab.treatments_df)

    # i_s = lab.treatments_df.set_index('treatment_id')['treatment_name']
    #
    # lab.skus_df['treatment_name'] = lab.skus_df['treatment_id'].map(i_s)
    # print(lab.skus_df)
    #
    # treatment_idx_df = lab.skus_df.set_index('treatment_id')
    #
    # lab.trs_df['treatment_name'] = lab.trs_df['treatment_id'].map(treatment_idx_df['treatment_name'])
    # lab.trs_df['tr_type'] = lab.trs_df['provider_id'].map(tr_type_s)
    # print(lab.trs_df)

    # treatments.= await lab.get_treatment_from_db_by_id(1)
    # print(treatments.treatment_name)

    # transaction = await lab.get_transaction_from_db_by_id(1)
    # print(transaction.timestamp)

    # skus = await lab.get_skus_from_db()
    # skus = await lab.get_sku_from_db_by_treatment_id(1)
    # for sku in skus.values():
    #     print(sku.treatment_id)
    #
    # trs = await lab.get_sessions_from_db_by_treatment_id(1)
    # for tr in trs.values():
    #     print(tr.session_id)

    # s_date = date.today()
    # e_date = date.today()
    # trs = await lab.get_sessions_from_db_by_date(s_date, e_date)
    # for tr in trs.values():
    #     print(tr.session_id)

if __name__ == '__main__':
    danaul_db = TreatmentsDb()
    lab = Lab(danaul_db)
    asyncio.run(main(lab))
