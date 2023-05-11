import asyncio
import asyncpg
from typing import List, Tuple
from asyncpg import Record
from asyncpg import UndefinedTableError
import logging
from datetime import date
from db_utils import connect_pg, ConnectPG
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

logging.basicConfig(level=logging.INFO)

class InventoryDB:
    def __init__(self, db_settings_file):
        self.connection: asyncpg.Connection = None
        self.db_settings = db_settings_file
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
        async with ConnectPG(self.db_settings) as conn:
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
        async with ConnectPG(self.db_settings) as conn:
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
            'category': [('Topical',), ('Fluid',), ('Orthotics',)],
            'item_side': [('Right',), ('Left',)],
            'item_size': [('Small',), ('Medium',), ('Large',), ('40cc',), ('120cc',)],
            'transaction_type': [('Buy',), ('Sell',), ('AdjustmentPlus',), ('AdjustmentMinus',)],
            'users': [('admin',), ('test',)]
        }
        async with ConnectPG(self.db_settings) as conn:
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
        '''
        Selecting all from the table
        :param table: table name
        :return: list of Record or None
        '''
        async with ConnectPG(self.db_settings) as conn:
            if conn is None:
                logging.debug('Error while connecting to DB during removing tables')
                return None

            try:
                query = await conn.prepare(f'SELECT $1 FROM {table}')
                results: List[Record] = await query.fetch('*')
                return results
            except Exception as e:
                logging.exception('Error while selecting sku table', e)
                return None

    async def query(self, statement: str, args: List[Tuple]):
        """

        :return: None
        """
        async with ConnectPG(self.db_settings) as conn:
            if conn is None:
                logging.debug('Error while connecting to DB during removing tables')
                return

            logging.info('Querying')
            try:
                await conn.executemany(statement, args)
            except Exception as e:
                logging.exception('Error during querying', e)

        logging.info('Finished querying')


async def main():
    danaul_db = InventoryDB('db_settings')
    # await danaul_db.create_tables()
    # await danaul_db.remove_tables()
    # await danaul_db.initialize_db()
    # await danaul_db.initial_insert()

    results = await danaul_db.select_all('item_side')
    print(results)


if __name__ == '__main__':
    asyncio.run(main())
