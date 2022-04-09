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
        sql_create_items_table = """ CREATE TABLE IF NOT EXISTS items (
                                            id integer PRIMARY KEY,
                                            code text NOT NULL,
                                            name text NOT NULL
                                        ); """

        sql_create_transactions_table = """CREATE TABLE IF NOT EXISTS transactions (
                                        id integer PRIMARY KEY,
                                        item_code text NOT NULL,
                                        category text NOT NULL,
                                        quantity integer NOT NULL,
                                        inventory integer NOT NULL,
                                        date text NOT NULL,
                                        FOREIGN KEY (item_code) REFERENCES items (code)
                                    );"""

        # create tables
        if self.connection is not None:
            # create items table
            self._create_table(sql_create_items_table)

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
        print(sql)
        cursor = self.connection.cursor()
        cursor.execute(*sql)
        self.connection.commit()
        return cursor

    def create_item(self, item):
        """
        Create a new item into the items table
        :param item:
        :return: item id
        """
        sql = ''' INSERT INTO items(code,name)
                  VALUES(?,?)'''
        cur = self._execute_sql(sql, item)
        return cur.lastrowid

    def create_transaction(self, transaction):
        """
        Create a new transaction
        :param transaction:
        :return: transaction id
        """
        sql = ''' INSERT INTO transactions(item_code,category,quantity,inventory,date)
                  VALUES(?,?,?,?,?) '''
        cur = self._execute_sql(sql, transaction)
        return cur.lastrowid

    def update_transaction(self, transaction):
        """
        Update(Modify) the transaction category, quantity, inventory, date
        :param transaction:
        :return:
        """
        sql = ''' UPDATE transactions
                  SET category = ?
                  SET quantity = ?
                  SET inventory = ?
                  SET date = ?
                  WHERE id = ? '''
        self._execute_sql(sql, transaction)

    def delete_item(self, id):
        """
        Delete a transaction by item id
        :param id:
        :return:
        """
        sql = 'DELETE FROM items WHERE id=?'
        self._execute_sql(sql, (id,))

    def delete_all_items(self):
        """
        Delete all rows in the items table
        :param
        :return:
        """
        sql = 'DELETE FROM items'
        self._execute_sql(sql)

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

    def select_all_items(self):
        """
        Query all rows in the items table
        :param
        :return: rows
        """
        sql = "SELECT * FROM items"
        cur = self._execute_sql(sql)
        rows = cur.fetchall()
        # for row in rows:
        #     print(row)

        return rows

    def select_item_by_code(self, code):
        """
        Query items by code
        :param priority:
        :return: rows
        """
        sql = "SELECT * FROM items WHERE item_code=?"
        cur = self._execute_sql(sql, (code,))
        rows = cur.fetchall()
        # for row in rows:
        #     print(row)

        return rows

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
        Query only the last transactions of each items
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
        items = [('AA', 'band'), ('BB', 'needle')]
        for item in items:
            inv_db.create_item(item)

        transactions = [
            ('AA', 'buy', 10, 10, date.today().isoformat()),
            ('BB', 'buy', 10, 10, date.today().isoformat()),
            ('AA', 'buy', 1, 11, date.today().isoformat()),
            ('CC', 'buy', 1, 11, date.today().isoformat()),
            ]
        for transaction in transactions:
            inv_db.create_transaction(transaction)

        rows = inv_db.select_all_items()
        dict = {v[1]: v[2:] for v in rows}
        print(dict)
        inv_db.select_transaction_by_code('DD')
        rows = inv_db.select_all_last_transactions()
        print(rows)
        dict = {v[1]: v[2:] for v in rows}
        print(dict)

        inv_db.delete_all_items()
        inv_db.delete_all_transactions()
