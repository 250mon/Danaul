import pandas as pd
import re
from typing import List
from db.db_utils import DbUtil, make_insert_query
from common.d_logger import Logs


logger = Logs().get_logger("db")


class DbApi:
    def __init__(self):
        self.db_util = DbUtil()

    async def create_tables(self, statements: List[str]):
        return await self.db_util.create_tables(statements)

    async def drop_tables(self, table_names: List[str]):
        # dropping is always in a reverse order from creating
        return await self.db_util.drop_tables(table_names[::-1])

    async def initialize_db(self, statements: List[str]):
        table_name_re = re.compile(r'''EXISTS\s+([a-z_]+)\s*\(''', re.MULTILINE)
        table_names = []
        for stmt in statements:
            name = table_name_re.findall(stmt)
            table_names += name

        await self.drop_tables(table_names)
        await self.create_tables(statements)

    async def insert_df(self, table_name: str, df: pd.DataFrame):
        # make a query statement part

        logger.debug(f"Insert into {table_name}...")
        logger.debug(f"\n{df}")

        # make a query argument part
        # we need to remove 'DEFAULT' from args
        non_default_df = df.loc[:, df.iloc[0, :] != 'DEFAULT']
        args = non_default_df.values.tolist()
        stmt = make_insert_query(table_name, non_default_df.to_dict('records')[0])

        logger.debug(stmt)
        logger.debug(args)
        # return await self.db_util.pool_execute(stmt, args)
        return await self.db_util.executemany(stmt, args)

    async def delete_df(self, table: str, del_df: pd.DataFrame):
        col_name, id_series = next(del_df.items())
        args = [(_id,) for _id in id_series]
        logger.debug(f"Delete {col_name} = {args} from {table} ...")
        return await self.db_util.delete(table, col_name, args)

    async def update_df(self, table: str, up_df: pd.DataFrame):
        col_names = up_df.columns
        id_name = col_names[0]
        place_holders = [f'{col_name}=${i}'for i, col_name in enumerate(col_names[1:], start=2)]
        ph_str = ','.join(place_holders)
        stmt = f"UPDATE {table} SET {ph_str} WHERE {id_name}=$1"
        args = [_tuple[1:] for _tuple in up_df.itertuples()]
        logger.debug(f"{stmt}")
        logger.debug(args)
        return await self.db_util.executemany(stmt, args)
