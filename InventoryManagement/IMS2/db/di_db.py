import pandas as pd
from typing import List
from db.db_utils import DbUtil
from db.inventory_schema import (
    CREATE_CATEGORY_TABLE,
    CREATE_ITEM_TABLE,
    CREATE_SKU_TABLE,
    CREATE_USER_TABLE,
    CREATE_TRANSACTION_TYPE_TABLE,
    CREATE_TRANSACTION_TABLE,
)
from common.d_logger import Logs


logger = Logs().get_logger("db")


class InventoryDb:
    def __init__(self):
        self.db_util = DbUtil()

    async def create_tables(self):
        statements = [CREATE_CATEGORY_TABLE,
                      CREATE_ITEM_TABLE,
                      CREATE_SKU_TABLE,
                      CREATE_USER_TABLE,
                      CREATE_TRANSACTION_TYPE_TABLE,
                      CREATE_TRANSACTION_TABLE]
        return await self.db_util.create_tables(statements)

    async def drop_tables(self):
        table_names = ['category', 'items', 'skus', 'users',
                       'transactions', 'transaction_type']
        # dropping is always in a reverse order from creating
        return await self.db_util.drop_tables(table_names[::-1])

    async def initialize_db(self):
        await self.drop_tables()
        await self.create_tables()

    async def insert_df(self, table: str, df: pd.DataFrame):
        def make_stmt(table_name: str, row_values: List):
            place_holders = []
            i = 1
            for val in row_values:
                if val == 'DEFAULT':
                    place_holders.append('DEFAULT')
                else:
                    place_holders.append(f'${i}')
                    i += 1
            stmt_value_part = ','.join(place_holders)
            stmt = f"INSERT INTO {table_name} VALUES({stmt_value_part})"
            return stmt
        logger.debug(f"Insert into {table}...")
        logger.debug(f"\n{df}")
        args = df.values.tolist()
        stmt = make_stmt(table, args[0])

        # we need to remove 'DEFAULT' from args
        non_default_df = df.loc[:, df.iloc[0, :] != 'DEFAULT']
        args = non_default_df.values.tolist()

        logger.debug(f"{stmt} {args}")
        # return await self.db_util.pool_execute(stmt, args)
        return await self.db_util.executemany(stmt, args)

    async def upsert_items_df(self, items_df: pd.DataFrame):
        """
        Insert items_df into DB, if the item_name pre-exists, update it
        :param items:
        :return:
        """
        stmt = """INSERT INTO items VALUES(DEFAULT, $1, $2, $3, $4)
                    ON CONFLICT (item_name)
                    DO
                     UPDATE SET active = $1,
                                item_name = $2,
                                category_id = $3,
                                description = $4"""
        args = [(item.active, item.item_name, item.category_id, item.description)
                for item in items_df.itertuples()]

        logger.debug("Upsert Items ...")
        logger.debug(args)
        return await self.db_util.executemany(stmt, args)

    async def delete_df(self, table: str, del_df: pd.DataFrame):
        # args = [(item.item_id,) for item in items_df.itertuples()]
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

    async def update_skus_df(self, skus_df: pd.DataFrame):
        """
        Update skus in DB from skus_df based on sku_id
        :param skus:
        :return:
        """
        stmt = """UPDATE skus SET active = $2,
                                  root_sku = $3,
                                  sub_name = $4,
                                  bit_code = $5,
                                  sku_qty = $6,
                                  min_qty = $7,
                                  item_id = $8,
                                  expiration_date = $9,
                                  description = $10
                              WHERE sku_id = $1"""
        args = [(sku.sku_id, sku.active, sku.root_sku, sku.sub_name,
                 sku.bit_code, sku.sku_qty, sku.min_qty, sku.item_id,
                 sku.expiration_date, sku.description)
                for sku in skus_df.itertuples()]
        logger.debug("Update Skus ...")
        logger.debug(args)
        return await self.db_util.executemany(stmt, args)

    async def delete_skus_df(self, skus_df: pd.DataFrame):
        args = [(sku_row.sku_id,) for sku_row in skus_df.itertuples()]
        logger.debug(f"Delete ids {args} from skus table ...")
        return await self.db_util.delete('skus', 'sku_id', args)

    async def update_trs_df(self, trs_df: pd.DataFrame):
        """
        Update trs in DB from trs_df based on tr_id
        :param trs:
        :return:
        """
        stmt = """UPDATE transactions SET user_id = $2,
                                          sku_id = $3,
                                          tr_type_id = $4,
                                          tr_qty = $5,
                                          before_qty = $6,
                                          after_qty = $7,
                                          tr_timestamp = $8,
                                          description = $9
                                      WHERE tr_id = $1"""
        args = [(tr.tr_id, tr.user_id, tr.sku_id, tr.tr_type,
                 tr.tr_qty, tr.before_qty, tr.after_qty, tr.timestamp,
                 tr.description)
                for tr in trs_df.itertuples()]
        logger.debug("Update Transactions ...")
        logger.debug(args)
        return await self.db_util.executemany(stmt, args)

    async def delete_trs_df(self, trs_df: pd.DataFrame):
        args = [(tr_row.tr_id,) for tr_row in trs_df.itertuples()]
        logger.debug(f"Delete ids {args} from transactions table ...")
        return await self.db_util.delete('transactions', 'tr_id', args)
