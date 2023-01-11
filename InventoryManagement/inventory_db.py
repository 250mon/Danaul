import sqlite3
from sqlite3 import Error
from datetime import date
import pyinputplus as pyip


class InventoryDB:
    def __init__(self, db_file):
        self.connection = self._create_connection(db_file)
        self._create_inventory_tables()

    def _create_connection(self, db_file):
        """
        Create a database connection to the SQLite database
        specified by db_file
        :param db_file:
        :return: Connection object or None
        """
        conn = None
        try:
            conn = sqlite3.connect(db_file)
        except Error as e:
            print(e)

        return conn

    def _create_table(self, create_table_sql):
        """ create a table from the create_table_sql statement
        :param conn: Connection object
        :param create_table_sql: a CREATE TABLE statement
        :return:
        """
        try:
            c = self.connection.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)

    def _create_inventory_tables(self):
        sql_create_transactions_table = """CREATE TABLE IF NOT EXISTS transactions (
                                        id integer PRIMARY KEY,
                                        item_code text NOT NULL,
                                        item_name text NOT NULL,
                                        category text NOT NULL,
                                        quantity integer NOT NULL,
                                        inventory integer NOT NULL,
                                        date text NOT NULL
                                    );"""

        # create tables
        if self.connection is not None:
            # create transactions table
            self._create_table(sql_create_transactions_table)
        else:
            print("Error! cannot create the database self.connection.")

    def _execute_sql(self, *sql):
        """
        Execute a sql statement
        :param sql:
        :return: cursor
        """
        cursor = self.connection.cursor()
        cursor.execute(*sql)
        self.connection.commit()
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

if __name__ == '__main__':
    inv_db = InventoryDB('test_inventory.db')

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
