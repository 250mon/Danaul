import re
import asyncio
from typing import List, Dict
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
            'providers': None,
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
        self.table_column_names['providers'] = ['provider_id', 'provider_name']
        self.table_column_names['sessions'] = col_name.findall(CREATE_SESSION_TABLE)

    async def _get_df_from_db(self, table: str, **kwargs) -> pd.DataFrame:
        logger.debug(f"{table}")

        if table == "users" and not self.show_inactive_items:
            query = f"SELECT * FROM {table} WHERE active = True"

        elif table == "sessions":
            main_part = f"SELECT * FROM sessions "
            where_part = ''
            time_part = ''
            limit_part = f"ORDER BY session_id DESC LIMIT {self.max_session_count}"
            if len(kwargs) > 0:
                beg_ts = kwargs.get('beg_timestamp', '')
                end_ts = kwargs.get('end_timestamp', '')
                if beg_ts != '' and end_ts != '':
                    time_part = f"WHERE timestamp >= '{beg_ts}' AND timestamp <= '{end_ts}' "

                if len(kwargs) == 3:
                    col_name = list(kwargs.keys())[2]
                    val = list(kwargs.values())[2]
                    where_part = f"AND {col_name} = {val} "
            query = main_part + time_part + where_part + limit_part

        elif table == "providers":
            query = ("SELECT user_id as provider_id, user_realname as provider_name "
                     "FROM users WHERE active = True and user_job = '물리치료'")

        else:
            query = f"SELECT * FROM {table}"

        logger.debug(query)

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

    def get_data_from_id(self, table: str, id: int, col: str) -> object:
        tdf = self.table_df[table]
        return tdf.loc[tdf.iloc[:, 0] == id, col].item()

    def get_id_from_data(self,
                         table: str,
                         data: Dict[str, object],
                         id_col_name: str) -> int:
        tdf = self.table_df[table]
        col, data = data.popitem()
        return tdf.loc[tdf.loc[:, col] == data, id_col_name].item()

    async def update_lab_df_from_db(self, table: str, **kwargs):
        logger.debug(f"table {table}")
        self.table_df[table] = await self._get_df_from_db(table, **kwargs)

    async def insert_df(self, table: str, new_df: pd.DataFrame):
        return await self.db_api.insert_df(table, new_df)

    async def update_df(self, table: str, up_df: pd.DataFrame):
        return await self.db_api.update_df(table, up_df)

    async def delete_df(self, table: str, del_df: pd.DataFrame):
        return await self.db_api.delete_df(table, del_df)
