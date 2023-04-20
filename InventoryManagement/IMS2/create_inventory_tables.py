import asyncio
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


async def main():
    connection = await connect_pg()
    if connection is None:
        print("Cannot connect to inventory DB!")
        exit(0)
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
    await connection.close()

asyncio.run(main())