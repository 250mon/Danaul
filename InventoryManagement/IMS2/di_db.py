import asyncio
import asyncpg
from typing import List
from asyncpg import Record
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
    SIDE_INSERT,
    SIZE_INSERT,
    TRANSACTION_TYPE_INSERT,
    USER_INSERT
)


class InventoryDB:
    def __init__(self, db_settings_file):
        self.connection: asyncpg.Connection = None
        self.db_settings = db_settings_file
        # self.create_connection()
        # self.create_tables()

    async def create_connection(self):
        """
        Create a database connection
        :param db_file:
        :return: Connection object or None
        """
        try:
            self.connection = await connect_pg(self.db_settings)
            if self.connection is None:
                print("Cannot connect to inventory DB!")
                exit(0)
        except Exception as e:
            logging.exception('Error while connecting to DB', e)


    async def create_tables(self):
        try:
            async with self.connection.transaction():
                statements = [CREATE_CATEGORY_TABLE,
                              CREATE_ITEM_TABLE,
                              CREATE_ITEM_SIZE_TABLE,
                              CREATE_ITEM_SIDE_TABLE,
                              CREATE_SKU_TABLE,
                              CREATE_USER_TABLE,
                              CREATE_TRANSACTION_TABLE,
                              CREATE_TRANSACTION_TYPE_TABLE,
                              SIDE_INSERT,
                              SIZE_INSERT,
                              TRANSACTION_TYPE_INSERT,
                              USER_INSERT]
                print('Creating the inventory database')
                for statement in statements:
                    status = await self.connection.execute(statement)
                    print(status)
                print('Finished creating the inventory database')
        except Exception as e:
            logging.exception('Error while creating tables', e)
        finally:
            print("closing DB ...")
            await self.connection.close()

    async def remove_tables(self):
        try:
            async with ConnectPG(self.db_settings) as connection:
                table_names = ['category', 'item', 'item_size',
                               'item_side', 'sku', 'users',
                               'transactions', 'transaction_type']
                sql_smt = 'DROP TABLE $1;'
                result = await connection.executemany(sql_smt, table_names)
                return result
        except Exception as e:
            logging.exception('Error while dropping tables', e)

    async def query(self):
        try:
            async with ConnectPG(self.db_settings) as conn:
                query = await conn.prepare('''SELECT $1 FROM users''')
                results: List[Record] = await query.fetch('admin')
                # query = await conn.prepare('''SELECT 1 + $1''')
                # results: int = await query.fetchval(2)
                return results
        except Exception as e:
            logging.exception('Error while dropping tables', e)

async def main():
    danaul_db = InventoryDB('db_settings')
    # await danaul_db.remove_tables()
    results = await danaul_db.query()
    print(results)

if __name__ == '__main__':
    asyncio.run(main())
