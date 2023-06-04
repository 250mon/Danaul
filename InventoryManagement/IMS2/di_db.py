import asyncio
from typing import List, Tuple
import logging
from db_utils import DbUtil
from di_logger import Logs
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
from data_classes import (
    Item, Sku, Transaction, EtcData, Category, ItemSide,
    ItemSize, TransactionType, User
)


class InventoryDb:
    def __init__(self, db_config_file):
        self.db_util = DbUtil(db_config_file)

        self.logs = Logs()
        self.logger = self.logs.get_logger('di_db')
        self.logger.setLevel(logging.DEBUG)

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
        return await self.db_util.drop_tables(table_names)

    async def initialize_db(self):
        await self.drop_tables()
        await self.create_tables()

    async def initial_insert(self, data: List[EtcData]):
        """
        Inserting initial data
        :return: None
        """
        stmt = f'INSERT INTO {data[0].table} VALUES($1, $2)'
        args = [(d.id, d.name) for d in data]
        return await self.db_util.sync_execute(stmt, args)

    async def insert_category(self, cat_name):
        stmt = "INSERT INTO category VALUES(DEFAULT, $1)"
        return await self.db_util.async_execute(stmt, [(cat_name), ])

    async def insert_items(self, items: List[Item]):
        """
        Initial insertion of items
        item_id and item_valid are set to default values
        :param items:
        :return:
        """
        stmt = "INSERT INTO items VALUES(DEFAULT, DEFAULT, $1, $2, $3)"
        args = [(item.item_name, item.category_id, item.description) for item in items]

        self.logger.debug("Insert Items ...")
        self.logger.debug(args)
        return await self.db_util.async_execute(stmt, args)

    async def delete_items(self, items: Item or List[Item]):
        if isinstance(items, List):
            args = [(item.item_id,) for item in items]
        elif isinstance(items, Item):
            args = [(items.item_id,)]
        else:
            msg = f"items' type{type(items)} must be either Item or List[Item]"
            self.logger.error(msg)
            return None

        self.logger.debug("Delete Items ...")
        self.logger.debug(args)
        return await self.db_util.delete('items', 'item_id', args)

    async def delete_items_by_name(self, item_names: str or List[str]):
        if isinstance(item_names, List):
            args = [(iname,) for iname in item_names]
        elif isinstance(item_names, str):
            args = [(item_names,)]
        else:
            msg = f"items' type{type(item_names)} must be either str or List[str]"
            self.logger.error(msg)
            return None

        self.logger.debug("Delete Items ...")
        self.logger.debug(args)
        return await self.db_util.delete('items', 'item_name', args)

    async def insert_skus(self, skus: List[Sku]):
        """
        Initial insertion of skus
        sku_id and sku_valid are set to default values
        :param skus:
        :return:
        """
        stmt = """INSERT INTO skus
                    VALUES(DEFAULT, DEFAULT, $1, $2, $3, $4, $5, $6, $7, $8)"""
        args = [(s.bit_code, s.sku_qty, s.min_qty, s.item_id, s.item_size_id,
                 s.item_side_id, s.expiration_date, s.description) for s in skus]

        self.logger.debug("Insert Skus ...")
        self.logger.debug(args)
        return await self.db_util.async_execute(stmt, args)

    async def delete_skus(self, skus: List[Sku]):
        args = [(s.sku_id,) for s in skus]

        self.logger.debug("Delete Skus ...")
        self.logger.debug(args)
        return await self.db_util.delete('skus', 'sku_id', args)

    async def insert_transactions(self, trs: List[Transaction]):
        """
        Transaction insertion must be done synchronously because of
        chronological order
        :param trs: list of transactions
        :return: results from DB
        """
        stmt = """INSERT INTO transactions
                    VALUES(DEFAULT, $1, $2, $3, $4, $5, $6, $7, $8)"""
        args = [(t.user_id, t.sku_id, t.tr_type_id,
                 t.tr_qty, t.before_qty, t.after_qty,
                 t.tr_timestamp, t.description) for t in trs]

        self.logger.debug("Insert Transactions ...")
        self.logger.debug(args)
        return await self.db_util.sync_execute(stmt, args)

    async def delete_transactions(self, trs: List[Transaction]):
        args = [(t.tr_id,) for t in trs]

        self.logger.debug("Delete Transactions ...")
        self.logger.debug(args)
        return await self.db_util.delete('transactions', 'tr_id', args)


async def main():
    danaul_db = InventoryDb('db_settings')

    # Initialize db by dropping all the tables and then
    # creating them all over again.
    # After creating the tables, inserting initial data
    async def initialize():
        await danaul_db.initialize_db()

        # initial insert
        etc_data = {
            'Category': ['외용제', '수액제', '보조기', '기타'],
            'ItemSide': ['None', 'Rt', 'Lt'],
            'ItemSize': ['None', 'Small', 'Medium', 'Large', '40cc', '120cc'],
            'TransactionType': ['Buy', 'Sell', 'AdjustmentPlus', 'AdjustmentMinus'],
            'User': ['admin', 'test']
        }
        for data_cls, data_list in etc_data.items():
            data_instances = []
            for i, _data in enumerate(data_list, start=1):
                # make a class instance for each element
                data_instance = globals()[data_cls](i, _data)
                data_instances.append(data_instance)
            await danaul_db.initial_insert(data_instances)

    async def insert_items():
        item_names = ['써지겔', '아토베리어', 'test1']
        items = [Item(None, True, name, 1) for name in item_names]

        # Inserting items
        print(await danaul_db.insert_items(items))

    async def delete_items():
        item_names = ['써지겔', '아토베리어', 'test1']

        # Deleting from the table
        # args = [('test1',),]
        # print(await danaul_db.db_util.delete('items', 'item_name', args))

        # Deleting items
        print(await danaul_db.delete_items_by_name(item_names))
        # Deleting item
        # print(await danaul_db.delete_items_by_name(items[0]))

    async def insert_skus():
        # Inserting skus
        skus = [Sku(None, True, 'aa', 9, 2, 3, 3),
                Sku(None, True, 'bb', 1, 2, 1, 3),
                Sku(None, True, 'cc', 3, 2, 2, 3)]
        print(await danaul_db.insert_skus(skus))

    async def insert_trs():
        # Inserting transactions
        trs = [Transaction(None, 1, 1, 1, 10, 0, 10, description='Initial'),
               Transaction(None, 2, 3, 1, 10, 0, 10, description='Initial'),
               Transaction(None, 1, 2, 1, 10, 0, 10),
               Transaction(None, 1, 1, 2, 10, 10, 0),
               Transaction(None, 1, 1, 1, 10, 0, 10),
               Transaction(None, 2, 3, 2, 5, 10, 5),
               Transaction(None, 1, 2, 2, 10, 10, 0),
               Transaction(None, 1, 1, 2, 10, 10, 0), ]
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
