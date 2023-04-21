import asyncio
import logging
from db_utils import connect_pg
from inventory_schema import (
    CREATE_CATEGORY_TABLE,
    CREATE_ITEM_TABLE,
    CREATE_ITEM_SIZE_TABLE,
    CREATE_ITEM_SIDE_TABLE,
    CREATE_SKU_TABLE,
    CREATE_USER_TABLE,
    CREATE_TRANSACTION_TABLE,
    SIDE_INSERT,
    SIZE_INSERT,
    USER_INSERT
)


async def create_tables():
    try:
        connection = await connect_pg()
        if connection is None:
            print("Cannot connect to inventory DB!")
            exit(0)
    except Exception as e:
        logging.exception('Error while connecting to DB', e)

    try:
        async with connection.transaction():
            statements = [CREATE_CATEGORY_TABLE,
                          CREATE_ITEM_TABLE,
                          CREATE_ITEM_SIZE_TABLE,
                          CREATE_ITEM_SIDE_TABLE,
                          CREATE_SKU_TABLE,
                          CREATE_USER_TABLE,
                          CREATE_TRANSACTION_TABLE,
                          SIDE_INSERT,
                          SIZE_INSERT,
                          USER_INSERT]
            print('Creating the inventory database')
            for statement in statements:
                status = await connection.execute(statement)
                print(status)
            print('Finished creating the inventory database')
    except Exception as e:
        logging.exception('Error while running transaction', e)
    finally:
        print("closing DB ...")
        await connection.close()


if __name__ == '__main__':
    asyncio.run(create_tables())