import asyncio
import asyncpg
from typing import List, Tuple
from asyncpg import Record
from asyncpg import UndefinedTableError
import logging
from functools import partial
from datetime import date
from db_utils import connect_pg, ConnectPG, DbConfig
# import pyinputplus as pyip
from inventory_schema import (
    CREATE_CATEGORY_TABLE,
    CREATE_ITEM_TABLE,
    CREATE_ITEM_SIZE_TABLE,
    CREATE_ITEM_SIDE_TABLE,
    CREATE_SKU_TABLE,
    CREATE_USER_TABLE,
    CREATE_TRANSACTION_TABLE,
    CREATE_TRANSACTION_TYPE_TABLE,
)
from lab import Lab
from items import Item, SKU, Transaction

logging.basicConfig(level=logging.DEBUG)

class InventoryDB:
    def __init__(self, db_config_file):
        self.connection: asyncpg.Connection = None
        self.db_config_file = db_config_file
        # self.create_connection()
        # self.create_tables()

    async def create_tables(self):
        """
        Create all the tables
        :return:  the list of results of creating the tables or None if connection fails
        """
        statements = [CREATE_CATEGORY_TABLE,
                      CREATE_ITEM_TABLE,
                      CREATE_ITEM_SIZE_TABLE,
                      CREATE_ITEM_SIDE_TABLE,
                      CREATE_SKU_TABLE,
                      CREATE_USER_TABLE,
                      CREATE_TRANSACTION_TABLE,
                      CREATE_TRANSACTION_TYPE_TABLE]

        results = []
        async with ConnectPG(self.db_config_file) as conn:
            if conn is None:
                logging.debug('Error while connecting to DB during removing tables')
                return

            logging.info('Creating the tables')
            for statement in statements:
                try:
                    logging.info(f'{statement}')
                    status = await conn.execute(statement)
                    results.append(status)
                    logging.debug(status)
                except Exception as e:
                    logging.exception(f'Error while creating table: {statement}', e)
            logging.info('Finished creating the tables')
        return results

    async def remove_tables(self):
        """
        Remove all the tables
        :return:  the list of results of dropping the tables or None if connection fails
        """
        table_names = ['category', 'item', 'item_size', 'item_side', 'sku', 'users',
                       'transactions', 'transaction_type']

        results = []
        async with ConnectPG(self.db_config_file) as conn:
            if conn is None:
                logging.debug('Error while connecting to DB during removing tables')
                return None

            logging.info('Removing the tables')
            for table in table_names:
                try:
                    sql_stmt = f'DROP TABLE {table} CASCADE;'
                    result = await conn.execute(sql_stmt)
                    results.append(result)
                except UndefinedTableError as ute:
                    logging.exception('Trying to drop an undefined table', ute)
                except Exception as e:
                    logging.exception('Error while dropping tables', e)
        logging.info('Finished removing the tables')
        return results

    async def initialize_db(self):
        """
        Remove all the tables and recreate them
        :return:
        """
        await self.remove_tables()
        await self.create_tables()

    async def initial_insert(self):
        """
        Inserting initial data
        :return: None
        """
        data = {
            'category': [('외용제',), ('수액제',), ('보조기',), ('기타',)],
            'item_side': [('Right',), ('Left',)],
            'item_size': [('Small',), ('Medium',), ('Large',), ('40cc',), ('120cc',)],
            'transaction_type': [('Buy',), ('Sell',), ('AdjustmentPlus',), ('AdjustmentMinus',)],
            'users': [('admin',), ('test',)]
        }
        async with ConnectPG(self.db_config_file) as conn:
            if conn is None:
                logging.debug('Error while connecting to DB during removing tables')
                return

            logging.info('Inserting initial data into the tables')
            for table, data_list in data.items():
                try:
                    stmt = f'INSERT INTO {table} VALUES(DEFAULT, $1)'
                    await conn.executemany(stmt, data_list)
                except Exception as e:
                    logging.exception('Error during initial insert', e)

        logging.info('Finished inserting initial data into the tables')

    async def select_all(self, table):
        """
        Selecting all from the table
        :param table: table name
        :return: list of Record or None
        """
        async with ConnectPG(self.db_config_file) as conn:
            if conn is None:
                logging.debug('Error while connecting to DB during removing tables')
                return None

            try:
                query = await conn.prepare(f'SELECT * FROM {table}')
                results: List[Record] = await query.fetch()
                return results
            except Exception as e:
                logging.exception('Error while selecting sku table', e)
                return None

    async def sync_execute(self, statement: str, args: List[Tuple]):
        """
        Execute a statement through connection.executemany()
        :param statement: statement to execute
        :param args: list of argements which are supplied to the statement one by one
        :return: list of results of queries
        """
        async with ConnectPG(self.db_config_file) as conn:
            if conn is None:
                logging.debug('Error while connecting to DB during removing tables')
                return

            logging.info('Synchronous executing')
            try:
                await conn.executemany(statement, args)
            except Exception as e:
                logging.exception('Error during synchronous executing', e)

        logging.info('Finished synchronous executing')

    async def async_execute(self, statement: str, args: List[Tuple]):
        """
        Execute a statement through ascynpg.pool
        :param statement: statement to execute
        :param args: list of argements which are supplied to the statement one by one
        :return: list of results of queries
        """
        async def execute(stmt, arg, pool):
            async with pool.acquire() as conn:
                logging.debug(stmt)
                logging.debug(arg)
                return await conn.execute(stmt, *arg)

        logging.info('Asynchronous executing')
        config_options = DbConfig(self.db_config_file)
        async with asyncpg.create_pool(host=config_options.host,
                                       port=config_options.port,
                                       user=config_options.user,
                                       database=config_options.database,
                                       password=config_options.passwd) as pool:
            queries = [execute(statement, arg, pool) for arg in args]
            results = await asyncio.gather(*queries)

            logging.info('Finished asynchronous executing')
            return results

    async def insert_category(self, cat_name):
        stmt = """ INSERT INTO category VALUES(DEFAULT, $1)"""
        await self.async_execute(stmt, [(cat_name),])

    async def insert_items(self, items: List[Item]):
        stmt = """ INSERT INTO item VALUES(DEFAULT, $1, $2)"""
        args = [(item.item_name, item.category_id) for item in items]
        logging.debug(args[0])
        await self.async_execute(stmt, args)


async def main():
    danaul_db = InventoryDB('db_settings')
    # await danaul_db.initialize_db()
    # await danaul_db.initial_insert()

    # results = await danaul_db.select_all('category')
    # print(results)

    items = [Item(None, '써지겔5', 1),]
    await danaul_db.insert_items(items)

    # stmt = """
    #     SELECT
    #         i.item_id,
    #         i.item_name,
    #         s.sku_id,
    #         s.sku_qty,
    #         isz.item_size_name,
    #         isd.item_side_name,
    #         s.expiration_date,
    #         c.category_name
    #     FROM item as i
    #     JOIN sku as s on s.item_id = i.item_id
    #     JOIN item_size as isz on isz.item_size_id = s.item_size_id
    #     JOIN item_side as isd on isd.item_side_id = s.item_side_id
    #     JOIN category as c on c.category_id = i.category_id
    #     WHERE i.item_id = 1
    #     """
    # results = await danaul_db.async_execute(stmt, [])
    # print(results)


if __name__ == '__main__':
    asyncio.run(main())
