import asyncio
import pandas as pd
import bcrypt
from db.di_db import InventoryDb


async def main():
    danaul_db = InventoryDb()

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
            'item_id':       ['DEFAULT', 'DEFAULT'],
            'active':        [True, True],
            'item_name':     ['노시셉톨', '써지겔'],
            'category_id':   [1, 1],
            'description':   ['', '']
        })
        print(await danaul_db.insert_df('items', items_df))

    async def insert_skus():
        skus_df = pd.DataFrame({
            'sku_id':           ['DEFAULT', 'DEFAULT', 'DEFAULT'],
            'active':           [True, True, True],
            'root_sku':         [0, 0, 0],
            'sub_name':         ['40ml', '120ml', ''],
            'bit_code':         ['noci40', 'noci120', 'surgigel'],
            'sku_qty':          [0, 0, 0],
            'min_qty':          [1, 1, 1],
            'item_id':          [1, 1, 2],
            'expiration_date':  ['DEFAULT', 'DEFAULT', 'DEFAULT'],
            'description':      ['', '', '']
        })
        print(await danaul_db.insert_df('skus', skus_df))

    async def insert_trs():
        # Inserting transactions
        trs_df = pd.DataFrame({
            'tr_id': ['DEFAULT'],
            'user_id': [1],
            'sku_id': [1],
            'tr_type_id': [1],
            'tr_qty': [0],
            'before_qty': [0],
            'after_qty': [0],
            'tr_timestamp': ['DEFAULT'],
            'description': ['']
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
                i.active,
                i.item_name,
                s.sku_id,
                s.active,
                s.sku_qty,
                s.min_qty,
                s.expiration_date,
                c.category_name
            FROM items as i
            JOIN skus as s using(item_id)
            JOIN category as c using(category_id)
               """
        print(await danaul_db.db_util.select_query(stmt))


if __name__ == '__main__':
    asyncio.run(main())
