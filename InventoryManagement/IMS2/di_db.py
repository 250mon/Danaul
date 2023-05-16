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
    CREATE_TRANSACTION_TYPE_TABLE,
    CREATE_TRANSACTION_TABLE,
)
from lab import Lab
from items import Item, Sku, Transaction

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
                      CREATE_TRANSACTION_TYPE_TABLE,
                      CREATE_TRANSACTION_TABLE]

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
        table_names = ['category', 'items', 'item_size', 'item_side', 'skus', 'users',
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
            'item_side': [('None',), ('Rt',), ('Lt',)],
            'item_size': [('None',), ('Small',), ('Medium',), ('Large',), ('40cc',), ('120cc',)],
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

    async def select_query(self, query):
        """
        Select query
        :param query
        :return: all results if successful, otherwise None
        """
        async with ConnectPG(self.db_config_file) as conn:
            if conn is None:
                logging.debug('Error while connecting to DB during removing tables')
                return None

            try:
                query = await conn.prepare(query)
                results: List[Record] = await query.fetch()
                return results
            except Exception as e:
                logging.exception(f'Error while executing {query}', e)
                return None

    async def sync_execute(self, statement: str, args: List[Tuple]):
        """
        Execute a statement through connection.executemany()
        :param statement: statement to execute
        :param args: list of arguments which are supplied to the statement one by one
        :return:
            if successful, None
            otherwise, exception or string
        """
        async with ConnectPG(self.db_config_file) as conn:
            if conn is None:
                logging.debug('Error while connecting to DB during removing tables')
                return "Connection failed"

            logging.info('Synchronous executing')
            try:
                results = await conn.executemany(statement, args)
                logging.info('Finished synchronous executing')
                return results
            except Exception as e:
                logging.exception('Error during synchronous executing', e)
                return e

    async def async_execute(self, statement: str, args: List[Tuple]):
        """
        Execute a statement through ascynpg.pool
        :param statement: statement to execute
        :param args: list of argements which are supplied to the statement one by one
        :return:
            if successful, list of results of queries
            otherwise, exception
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
            results = await asyncio.gather(*queries, return_exceptions=True)
            logging.info('Finished asynchronous executing')
            return results

    async def delete(self, table, col_name, args: List[Tuple]):
        if not isinstance(args, List):
            logging.error(f"args' type{type(args)} must be List[Tuple]")
            return None
        if not isinstance(args[0], Tuple):
            logging.error(f"args element's type{type(args[0])} must be Tuple")
            return None

        stmt = f"DELETE FROM {table} WHERE {col_name} = $1"
        logging.debug(args)
        return await self.async_execute(stmt, args)

    async def insert_category(self, cat_name):
        stmt = "INSERT INTO category VALUES(DEFAULT, $1)"
        return await self.async_execute(stmt, [(cat_name),])

    async def insert_items(self, items: List[Item]):
        """
        Initial insertion of items
        item_id and item_valid are set to default values
        :param items:
        :return:
        """
        stmt = "INSERT INTO items VALUES(DEFAULT, DEFAULT, $1, $2)"
        args = [(item.item_name, item.category_id) for item in items]
        logging.debug(args[0])
        return await self.async_execute(stmt, args)

    async def delete_items(self, items: Item or List[Item]):
        if isinstance(items, List):
            args = [(item.item_id,) for item in items]
        elif isinstance(items, Item):
            args = [(items.item_id,)]
        else:
            logging.error(f"items' type{type(items)} must be either Item or List[Item]")
            return None

        return await self.delete('items', 'item_id', args)

    async def delete_items_by_name(self, item_names: str or List[str]):
        if isinstance(item_names, List):
            args = [(iname,) for iname in item_names]
        elif isinstance(item_names, str):
            args = [(item_names,)]
        else:
            logging.error(f"items' type{type(items)} must be either Item or List[Item]")
            return None

        return await self.delete('items', 'item_name', args)

    async def insert_skus(self, skus: List[Sku]):
        """
        Initial insertion of skus
        sku_id and sku_valid are set to default values
        :param skus:
        :return:
        """
        stmt = """INSERT INTO skus
                    VALUES(DEFAULT, DEFAULT, $1, $2, $3, $4, $5, $6)"""
        args = [(s.bit_code, s.sku_qty, s.item_id, s.item_size_id,
                 s.item_side_id, s.expiration_date) for s in skus]
        return await self.async_execute(stmt, args)

    async def delete_skus(self, skus: List[Sku]):
        args = [(s.sku_id,) for s in skus]
        return await self.delete('skus', 'sku_id', args)

    async def insert_transactions(self, trs: List[Transaction]):
        """
        Transaction insertion must be done synchronously because of
        chronological order
        :param trs: list of transactions
        :return: results from DB
        """
        stmt = """INSERT INTO transactions
                    VALUES(DEFAULT, $1, $2, $3, $4, $5, $6, $7)"""
        args = [(t.user_id, t.sku_id, t.tr_type_id,
                 t.tr_qty, t.before_qty, t.after_qty,
                 t.tr_datetime) for t in trs]
        return await self.sync_execute(stmt, args)

    async def delete_transactions(self, trs: List[Transaction]):
        args = [(t.tr_id,) for t in trs]
        return await self.delete('transactions', 'tr_id', args)


async def main():
    danaul_db = InventoryDB('db_settings')
    # Initialize db by dropping all the tables and then
    # creating them all over again.
    # After creating the tables, inserting initial data
    async def initialize():
        await danaul_db.initialize_db()
        await danaul_db.initial_insert()

    async def insert_items():
        item_names = ['써지겔', '아토베리어', 'test1']
        items = [Item(None, True, name, 1) for name in item_names]

        # Inserting items
        print(await danaul_db.insert_items(items))

    async def delete_items():
        item_names = ['써지겔', '아토베리어', 'test1']

        # Deleting from the table
        # args = [('test1',),]
        # print(await danaul_db.delete('items', 'item_name', args))

        # Deleting items
        print(await danaul_db.delete_items_by_name(item_names))
        # Deleting item
        # print(await danaul_db.delete_items_by_name(items[0]))

    async def insert_skus():
        # Inserting skus
        skus = [Sku(None, True, 'aa', 10, 3, 3), Sku(None, True, 'bb', 1, 1, 3),
                Sku(None, True, 'cc', 3, 2, 3)]
        print(await danaul_db.insert_skus(skus))

    async def insert_trs():
        # Inserting transactions
        trs = [Transaction(None, 1, 1, 1, 10, 0, 10),
               Transaction(None, 2, 3, 1, 10, 0, 10),
               Transaction(None, 1, 2, 1, 10, 0, 10),
               Transaction(None, 1, 1, 2, 10, 10, 0),
               Transaction(None, 1, 1, 1, 10, 0, 10),
               Transaction(None, 2, 3, 2, 5, 10, 5),
               Transaction(None, 1, 2, 2, 10, 10, 0),
               Transaction(None, 1, 1, 2, 10, 10, 0),]
        print(await danaul_db.insert_transactions(trs))

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
                isz.item_size,
                isd.item_side,
                s.expiration_date,
                c.category_name
            FROM items as i
            JOIN skus as s using(item_id)
            JOIN item_size as isz using(item_size_id)
            JOIN item_side as isd using(item_side_id)
            JOIN category as c using(category_id);
               """
        print(await danaul_db.select_query(stmt))
        
    await select_item()


    # stmt = """
    #     SELECT
    #         i.item_id,
    #         i.item_name,
    #         s.sku_id,
    #         s.sku_qty,
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
    # results = await danaul_db.async_execute(stmt, [])
    # print(results)


if __name__ == '__main__':
    asyncio.run(main())
