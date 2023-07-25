import os
import asyncio
import pandas as pd
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
from IMS2.unused.data_classes import Item, Sku, Transaction
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

    async def insert_extras_df(self, table: str, extras_df: pd.DataFrame):
        """
        Initial insertion of extras_df
        :param extras_df:
        :return:
        """
        if table != 'users':
            stmt = f"INSERT INTO {table} VALUES(DEFAULT, $1)"
        else:
            stmt = f"INSERT INTO {table} VALUES(DEFAULT, $1, DEFAULT)"
        args = [(extra.name,) for extra in extras_df.itertuples()]

        logger.debug(f"Insert {table}...")
        logger.debug(args)
        # use executemany for sequential indexing of ids
        return await self.db_util.executemany(stmt, args)

    async def insert_df(self, table: str, df: pd.DataFrame, default_id: bool = False):
        def make_stmt(table_name: str, nargs: int, default_id: bool):
            if default_id:
                id_part = "DEFAULT,"
                nargs = nargs - 1
            else:
                id_part = ""
            args_part = ",".join(["$" + str(i) for i in range(1, nargs + 1)])
            stmt = f"INSERT INTO {table_name} VALUES({id_part}{args_part})"
            return stmt

        logger.debug(f"insert_df: Insert into {table}...")
        logger.debug(f"insert_df: \n{df}")
        stmt = make_stmt(table, len(df.columns), default_id)
        args = df.values.tolist()
        if default_id:
            # id is removed and set DEFAULT
            # args = [[id1, f11, f21, ...], [id2, f12, f22, ...], ...]
            args = [l[1:] for l in args]

        logger.debug(f"insert_df: {stmt} {args}")
        # return await self.db_util.pool_execute(stmt, args)
        return await self.db_util.executemany(stmt, args)

    async def upsert_items_df(self, items_df: pd.DataFrame):
        """
        Initial insertion of items
        item_id and item_valid are set to default values
        :param items:
        :return:
        """
        stmt = """INSERT INTO items VALUES(DEFAULT, DEFAULT, $2, $3, $4)
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
        return await self.db_util.pool_execute(stmt, args)

    async def delete_items_df(self, items_df: pd.DataFrame):
        args = [(item.item_id,) for item in items_df.itertuples()]
        logger.debug(f"delete_record: Delete ids {args} from items table ...")
        return await self.db_util.delete('items', 'item_id', args)

    async def insert_items(self, items: List[Item]):
        """
        Initial insertion of items
        item_id and item_valid are set to default values
        :param items:
        :return:
        """
        stmt = "INSERT INTO items VALUES(DEFAULT, DEFAULT, $1, $2, $3)"
        args = [(item.item_name, item.category_id, item.description) for item in items]

        logger.debug("Insert Items ...")
        logger.debug(args)
        return await self.db_util.pool_execute(stmt, args)

    async def delete_items(self, items: Item or List[Item]):
        if isinstance(items, List):
            args = [(item.item_id,) for item in items]
        elif isinstance(items, Item):
            args = [(items.item_id,)]
        else:
            msg = f"items' type{type(items)} must be either Item or List[Item]"
            logger.error(msg)
            return None

        logger.debug("Delete Items ...")
        logger.debug(args)
        return await self.db_util.delete('items', 'item_id', args)

    async def delete_items_by_name(self, item_names: str or List[str]):
        if isinstance(item_names, List):
            args = [(iname,) for iname in item_names]
        elif isinstance(item_names, str):
            args = [(item_names,)]
        else:
            msg = f"items' type{type(item_names)} must be either str or List[str]"
            logger.error(msg)
            return None

        logger.debug("Delete Items ...")
        logger.debug(args)
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

        logger.debug("Insert Skus ...")
        logger.debug(args)
        return await self.db_util.pool_execute(stmt, args)

    async def delete_skus(self, skus: List[Sku]):
        args = [(s.sku_id,) for s in skus]

        logger.debug("Delete Skus ...")
        logger.debug(args)
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

        logger.debug("Insert Transactions ...")
        logger.debug(args)
        return await self.db_util.executemany(stmt, args)

    async def delete_transactions(self, trs: List[Transaction]):
        args = [(t.tr_id,) for t in trs]

        logger.debug("Delete Transactions ...")
        logger.debug(args)
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
        extra_data['users'] = pd.DataFrame({
            'id': [1, 2],
            'name': ['admin', 'test'],
            'pw': [b'\x00', b'\x00']
        })
        for table, data_df in extra_data.items():
            # make dataframe for each table
            await danaul_db.insert_df(table, data_df, default_id=True)

    async def insert_items():
        item_names = ['써지겔', '아토베리어', 'test1']
        items = [Item(None, True, name, 1) for name in item_names]

        # Inserting items
        print(await danaul_db.insert_items(items))

    async def delete_items():
        item_names = ['써지겔', '아토베리어', 'test1']

        # Deleting items
        print(await danaul_db.delete_items_by_name(item_names))
        # Deleting item
        # print(await danaul_db.delete_items_by_name(items[0]))

    async def insert_skus():
        # Inserting skus
        skus = [Sku(None, True, 'aa', 9, 2, 3, 2),
                Sku(None, True, 'bb', 1, 2, 2, 3),
                Sku(None, True, 'cc', 3, 2, 2, 2)]
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
