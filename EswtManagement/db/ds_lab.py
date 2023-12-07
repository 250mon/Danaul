import re
import asyncio
from typing import List
from db.db_apis import DbApi
import pandas as pd
from common.d_logger import Logs
from constants import MAX_SESSION_COUNT
from common.singleton import Singleton
from db.db_schema import *


logger = Logs().get_logger("db")

class Lab(metaclass=Singleton):
    def __init__(self):
        self.db_api = DbApi()
        self.di_db_util = self.db_api.db_util
        self.max_session_count = MAX_SESSION_COUNT
        self.show_inactive_items = False

        self.table_df = {
            'category': None,
            'modalities': None,
            'patients': None,
            'users': None,
            'body_parts': None,
            'sessions': None,
            'active_providers': None,
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
                logger.debug(f"Retrieved DB data \n{df}")
            for table in reversed(self.table_df.keys()):
                self.table_df[table] = data_dfs.pop()

            # make reference series
            self._make_ref_series()

        self.bool_initialized = True
        return self

    def __await__(self):
        return self.async_init().__await__()

    def _set_max_session_count(self, count: int):
        if count > 0:
            self.max_session_count = count
        else:
            logger.warn(f""
                        f"count({count}) is not a positive integer")

    def _set_db_column_names(self):
        col_name = re.compile(r'''^\s*([a-z_]+)\s*''', re.MULTILINE)
        self.table_column_names = {}
        self.table_column_names['patients'] = col_name.findall(CREATE_PATIENT_TABLE)

    async def _get_df_from_db(self, table: str, **kwargs) -> pd.DataFrame:
        logger.debug(f"{table}")
        where_clause = ""
        # if not self.show_inactive_items:
        #     if table == "treatments":
        #         where_clause = " WHERE active = True"
        #     elif table == "skus":
        #         where_clause = " WHERE (treatment_id IN (SELECT treatment_id FROM treatments WHERE active = True)) AND " \
        #                        "(active = True)"
        #     elif table == "sessions":
        #         where_clause = " WHERE treatment_id IN (SELECT treatment_id FROM skus AS s WHERE " \
        #                        "(s.treatment_id IN (SELECT treatment_id FROM treatments AS i WHERE i.active = True)) AND " \
        #                        "(s.active = True))"

        if table == "sessions":
            patient_id = kwargs.get('patient_id', None)
            beg_ts = kwargs.get('beg_timestamp', '')
            end_ts = kwargs.get('end_timestamp', '')
            if patient_id is None:
                query = f"SELECT * FROM sessions {where_clause} ORDER BY session_id DESC LIMIT " \
                        f"{self.max_session_count}"
            else:
                if beg_ts != '' and end_ts != '':
                    query = f"SELECT * FROM sessions WHERE patient_id = {patient_id} " \
                            f"AND timestamp >= '{beg_ts}' AND timestamp <= '{end_ts}' " \
                            f"ORDER BY session_id DESC LIMIT {self.max_session_count}"
                else:
                    # beg_ts == '' or end_ts == '':
                    query = f"SELECT * FROM sessions WHERE patient_id = {patient_id} " \
                            f"ORDER BY session_id DESC LIMIT {self.max_session_count}"

            where_clause = ""

        elif table == "active_providers":
            query = ("SELECT user_id as provider_id, user_name as provider_name"
                     " FROM users active = 'True' and user_job = '물리치료'")

        else:
            query = f"SELECT * FROM {table}"

        query = query + where_clause
        logger.debug(f"{query}")

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

        self.category_id_s = make_series('category', False)
        self.category_name_s = make_series('category', True)
        self.modality_id_s = make_series('modalities', False)
        self.modality_name_s = make_series('modalities', True)
        self.patient_id_s = make_series('patients', False)
        self.patient_name_s = make_series('patients', True)
        self.user_id_s = make_series('users', False)
        self.user_name_s = make_series('users', True)

    def get_data_from_id(self, table: str, id: int, col: str) -> object:
        tdf = self.table_df[table]
        return tdf.loc[tdf.iloc[:, 0] == id, col].item()

    def get_id_from_data(self, table: str, data: object, col: str) -> int:
        tdf = self.table_df[table]
        return tdf.iloc[tdf.loc[:, col] == data, 0].item()

    async def update_lab_df_from_db(self, table: str, **kwargs):
        logger.debug(f"table {table}")
        self.table_df[table] = await self._get_df_from_db(table, **kwargs)

    async def insert_df(self, table: str, new_df: pd.DataFrame):
        return await self.db_api.insert_df(table, new_df)

    async def update_df(self, table: str, up_df: pd.DataFrame):
        return await self.db_api.update_df(table, up_df)

    async def delete_df(self, table: str, del_df: pd.DataFrame):
        return await self.db_api.delete_df(table, del_df)
