import asyncio
import logging
from datetime import date
from db_utils import connect_pg
import asyncpg
import pyinputplus as pyip
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


class InventoryDB:
    def __init__(self, db_settings_file):
        self.connection: asyncpg.Connection = None
        self._create_connection(db_settings_file)
        self._create_tables()

    def _create_connection(self):
        """
        Create a database connection
        :param db_file:
        :return: Connection object or None
        """
        try:
            self.connection = await connect_pg()
            if self.connection is None:
                print("Cannot connect to inventory DB!")
                exit(0)
        except Exception as e:
            logging.exception('Error while connecting to DB', e)


    async def _create_tables(self):
        try:
            async with self.connection.transaction():
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
                    status = await self.connection.execute(statement)
                    print(status)
                print('Finished creating the inventory database')
        except Exception as e:
            logging.exception('Error while running transaction', e)
        # finally:
        #     print("closing DB ...")
        #     await self.connection.close()

    def _execute_sql(self, *sql):
        """
        Execute a sql statement
        :param sql:
        :return: cursor
        """
        cursor = self.connection.cursor()
        cursor.execute(*sql)
        return cursor

    def create_transaction(self, transaction):
        """
        Create a new transaction
        :param transaction:
        :return: transaction id
        """
        sql = ''' INSERT INTO transactions(item_code,item_name,category,quantity,inventory,date)
                  VALUES(?,?,?,?,?,?) '''
        cur = self._execute_sql(sql, transaction)
        return cur.lastrowid

    def update_transaction(self, transaction):
        """
        Update(Modify) the transaction category, quantity, inventory, date
        :param transaction:
        :return:
        """
        sql = ''' UPDATE transactions
                  SET category = ?, quantity = ?, inventory = ?
                  WHERE id = ? '''
        self._execute_sql(sql, transaction)

    def delete_transaction(self, id):
        """
        Delete a transaction by transaction id
        :param id:
        :return:
        """
        sql = 'DELETE FROM transactions WHERE id=?'
        self._execute_sql(sql, (id,))

    def delete_all_transactions(self):
        """
        Delete all rows in the transactions table
        :param
        :return:
        """
        sql = 'DELETE FROM transactions'
        self._execute_sql(sql)

    def select_all_transactions(self):
        """
        Query all rows in the transactions table
        :param
        :return: rows
        """
        sql = "SELECT * FROM transactions"
        cur = self._execute_sql(sql)
        rows = cur.fetchall()
        # for row in rows:
        #     print(row)

        return rows

    def select_all_last_transactions(self):
        """
        Query only the last transactions of each item
        :param
        :return:
        """
        sql = "SELECT * FROM transactions" \
              " WHERE id in (SELECT MAX(id) FROM transactions GROUP BY item_code) ORDER BY id DESC"
        cur = self._execute_sql(sql)
        rows = cur.fetchall()
        return rows

    def select_transaction_by_code(self, code):
        """
        Query transactions by code
        :param code:
        :return:
        """
        sql = "SELECT * FROM transactions WHERE item_code=?"
        cur = self._execute_sql(sql, (code,))
        rows = cur.fetchall()
        # for row in rows:
        #     print(row)

        return rows

async def main():
    inv_db = InventoryDB()

    with inv_db.connection:
        transactions = [
            ('AA', 'band', 'inbound', 10, 10, date.today().isoformat()),
            ('BB', 'needle', 'inbound', 10, 10, date.today().isoformat()),
            ('AA', 'band', 'inbound', 1, 11, date.today().isoformat()),
            ('CC', '거즈', 'inbound', 1, 11, date.today().isoformat()),
            ]
        for transaction in transactions:
            inv_db.create_transaction(transaction)

        # rows = inv_db.select_transaction_by_code('DD')
        # print(rows)
        # rows = inv_db.select_all_last_transactions()
        # print(rows)
        # dict = {v[1]: v[2:] for v in rows}
        # print(dict)
        # modify_trans = ('inbound', 10, 10, 18)
        # inv_db.update_transaction(modify_trans)
        rows = inv_db.select_all_transactions()
        for row in rows:
            print(row)
        # inv_db.delete_all_transactions()

if __name__ == '__main__':
    asyncio.run(main())
