import os
import asyncio
import pandas as pd
import bcrypt
from typing import List
from db_utils import DbUtil
from inventory_schema import (
    CREATE_CATEGORY_TABLE,
    CREATE_ITEM_TABLE,
    CREATE_ITEM_SIZE_TABLE,
    CREATE_ITEM_SIDE_TABLE,
    CREATE_SKU_TABLE,
    CREATE_USER_TABLE,
    CREATE_TRANSACTION_TYPE_TABLE,
    CREATE_TRANSACTION_TABLE,
)
from di_logger import Logs, logging


logger = Logs().get_logger(os.path.basename(__file__))
logger.setLevel(logging.DEBUG)


class InventoryDb:
    def __init__(self, db_config_file):
        self.db_util = DbUtil(db_config_file)

    async def create_tables(self):
        statements = [CREATE_CATEGORY_TABLE,
                      CREATE_ITEM_TABLE,
                      CREATE_ITEM_SIZE_TABLE,
                      CREATE_ITEM_SIDE_TABLE,
                      CREATE_SKU_TABLE,
                      CREATE_USER_TABLE,
                      CREATE_TRANSACTION_TYPE_TABLE,
                      CREATE_TRANSACTION_TABLE]
        return await self.db_util.create_tables(statements)

    async def drop_tables(self):
        table_names = ['category', 'items', 'item_size', 'item_side', 'skus', 'users',
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
        logger.debug(f"insert_df: Insert into {table}...")
        logger.debug(f"insert_df: \n{df}")
        args = df.values.tolist()
        stmt = make_stmt(table, args[0])

        # we need to remove 'DEFAULT' from args
        non_default_df = df.loc[:, df.loc[0, :] != 'DEFAULT']
        args = non_default_df.values.tolist()

        logger.debug(f"insert_df: {stmt} {args}")
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
                     UPDATE SET item_valid = $1,
                                item_name = $2,
                                category_id = $3,
                                description = $4"""
        args = [(item.item_valid, item.item_name, item.category_id, item.description)
                for item in items_df.itertuples()]

        logger.debug("Upsert Items ...")
        logger.debug(args)
        return await self.db_util.executemany(stmt, args)

    async def delete_items_df(self, items_df: pd.DataFrame):
        args = [(item.item_id,) for item in items_df.itertuples()]
        logger.debug(f"delete_record: Delete ids {args} from items table ...")
        return await self.db_util.delete('items', 'item_id', args)

    async def update_skus_df(self, skus_df: pd.DataFrame):
        """
        Update skus in DB from skus_df based on sku_id
        :param skus:
        :return:
        """
        stmt = """UPDATE skus SET sku_valid = $2,
                                  bit_code = $3,
                                  sku_qty = $4,
                                  min_qty = $5,
                                  item_id = $6,
                                  item_size_id = $7,
                                  item_side_id = $8,
                                  expiration_date = $9,
                                  description = $10
                              WHERE sku_id = $1"""
        args = [(sku.sku_id, sku.sku_valid, sku.bit_code, sku.sku_qty,
                 sku.min_qty, sku.item_id, sku.item_size_id, sku.item_side_id,
                 sku.expiration_date, sku.description)
                for sku in skus_df.itertuples()]
        logger.debug("Update Skus ...")
        logger.debug(args)
        return await self.db_util.executemany(stmt, args)

    async def delete_skus_df(self, skus_df: pd.DataFrame):
        args = [(sku_row.sku_id,) for sku_row in skus_df.itertuples()]
        logger.debug(f"delete_record: Delete ids {args} from skus table ...")
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
        logger.debug(f"delete_record: Delete ids {args} from transactions table ...")
        return await self.db_util.delete('transactions', 'tr_id', args)

async def main():
    danaul_db = InventoryDb('db_settings')

    # Initialize db by dropping all the tables and then
    # creating them all over again.
    # After creating the tables, inserting initial data
    async def initialize():
        await danaul_db.initialize_db()

        extra_data = {}
        # initial insert
        extra_data['category'] = pd.DataFrame({
            'id': [1, 2, 3, 4],
            'name': ['외용제', '수액제', '보조기', '기타']
        })

        extra_data['item_side'] = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['None', 'Rt', 'Lt']
        })

        extra_data['item_size'] = pd.DataFrame({
            'id': [1, 2, 3, 4, 5, 6],
            'name': ['None', 'Small', 'Medium', 'Large', '40cc', '120cc']
        })

        extra_data['transaction_type'] = pd.DataFrame({
            'id': [1, 2, 3, 4],
            'name': ['Buy', 'Sell', 'AdjustmentPlus', 'AdjustmentMinus']
        })
        def encrypt_password(password):
            # Generate a salt and hash the password
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed_password

        encrypted_pw = encrypt_password('a')
        extra_data['users'] = pd.DataFrame({
            'id': [1, 2],
            'name': ['admin', 'test'],
            'pw': [encrypted_pw, encrypted_pw]
        })

        for table, data_df in extra_data.items():
            # make dataframe for each table
            await danaul_db.insert_df(table, data_df)

    async def insert_items():
        items_df = pd.DataFrame({
            'item_id':       [1, 2, 3],
            'item_valid':    [True, True, True],
            'item_name':     ['써지겔', '아토베리어', 'test1'],
            'category_id':   [1, 1, 1],
            'description':   ['', '', '']
        })
        print(await danaul_db.insert_df('items', items_df))

    async def insert_skus():
        skus_df = pd.DataFrame({
            'sku_id':           [1, 2, 3],
            'sku_valid':        [True, True, True],
            'bit_code':         ['bb', 'cc', 'aa'],
            'sku_qty':          [1, 3, 9],
            'min_qty':          [2, 2, 2],
            'item_id':          [2, 2, 3],
            'item_size_id':     [3, 2, 2],
            'item_side_id':     [1, 1, 1],
            'expiration_date':  ['DEFAULT', 'DEFAULT', 'DEFAULT'],
            'description':      ['', '', '']
        })
        print(await danaul_db.insert_df('skus', skus_df))

    async def insert_trs():
        # Inserting transactions
        trs_df = pd.DataFrame({
            'tr_id': ['DEFAULT', 'DEFAULT', 'DEFAULT', 'DEFAULT', 'DEFAULT', 'DEFAULT'],
            'user_id':[1, 2, 1, 1, 1, 2],
            'sku_id': [1, 3, 2, 1, 1, 3],
            'tr_type_id': [1, 1, 1, 2, 1, 2],
            'tr_qty': [10, 10, 10, 10, 10, 5],
            'before_qty': [0, 0, 0, 10, 0, 10],
            'after_qty': [10, 10, 10, 0, 10, 5],
            'tr_timestamp': ['DEFAULT', 'DEFAULT', 'DEFAULT', 'DEFAULT', 'DEFAULT', 'DEFAULT'],
            'description': ['', '', '', '', '', '']
        })
        print(await danaul_db.insert_df('transactions', trs_df))

    await initialize()
    await insert_items()
    await insert_skus()
    await insert_trs()

    # await delete_items()

    # Select from a table
    async def select_item():
        stmt = """
            SELECT
                i.item_id,
                i.item_valid,
                i.item_name,
                s.sku_id,
                s.sku_valid,
                s.sku_qty,
                s.min_qty,
                isz.item_size,
                isd.item_side,
                s.expiration_date,
                c.category_name
            FROM items as i
            JOIN skus as s using(item_id)
            JOIN item_size as isz using(item_size_id)
            JOIN item_side as isd using(item_side_id)
            JOIN category as c using(category_id)
               """
        print(await danaul_db.db_util.select_query(stmt))

    # await select_item()

    # stmt = """
    #     SELECT
    #         i.item_id,
    #         i.item_name,
    #         s.sku_id,
    #         s.sku_qty,
    #         s.min_qty,
    #         isz.item_size,
    #         isd.item_side_name,
    #         s.expiration_date,
    #         c.category_name
    #     FROM item as i
    #     JOIN skus as s on s.item_id = i.item_id
    #     JOIN item_size as isz on isz.item_size_id = s.item_size_id
    #     JOIN item_side as isd on isd.item_side_id = s.item_side_id
    #     JOIN category as c on c.category_id = i.category_id
    #     WHERE i.item_id = 1
    #     """
    # results = await danaul_db.db_util.async_execute(stmt, [])
    # print(results)


if __name__ == '__main__':
    asyncio.run(main())
