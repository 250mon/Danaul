import sqlite3
from sqlite3 import Error
from datetime import date


def create_connection(db_file):
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

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def create_inventory_tables(db_file):
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

    # create a database connection
    conn = create_connection(db_file)

    # create tables
    if conn is not None:
        # create items table
        create_table(conn, sql_create_items_table)

        # create transactions table
        create_table(conn, sql_create_transactions_table)
    else:
        print("Error! cannot create the database connection.")
    conn.close()

def create_item(conn, item):
    """
    Create a new item into the items table
    :param conn:
    :param item:
    :return: item id
    """
    sql = ''' INSERT INTO items(code,name)
              VALUES(?,?)'''
    cur = conn.cursor()
    cur.execute(sql, item)
    conn.commit()
    return cur.lastrowid

def create_transaction(conn, transaction):
    """
    Create a new transaction
    :param conn:
    :param transaction:
    :return: transaction id
    """
    sql = ''' INSERT INTO transactions(item_code,category,quantity,inventory,date)
              VALUES(?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, transaction)
    conn.commit()
    return cur.lastrowid

def update_transaction(conn, transaction):
    """
    Update(Modify) the transaction category, quantity, inventory, date
    :param conn:
    :param transaction:
    :return:
    """
    sql = ''' UPDATE transactions
              SET category = ?
              SET quantity = ?
              SET inventory = ?
              SET date = ?
              WHERE id = ? '''
    cur = conn.cursor()
    cur.execute(sql, transaction)
    conn.commit()

def delete_item(conn, id):
    """
    Delete a transaction by item id
    :param conn:
    :param id:
    :return:
    """
    sql = 'DELETE FROM items WHERE id=?'
    cur = conn.cursor()
    cur.execute(sql, (id,))
    conn.commit()

def delete_all_items(conn):
    """
    Delete all rows in the items table
    :param conn: Connection to the SQLite database
    :return:
    """
    sql = 'DELETE FROM items'
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()

def delete_transaction(conn, id):
    """
    Delete a transaction by transaction id
    :param conn:
    :param id:
    :return:
    """
    sql = 'DELETE FROM transactions WHERE id=?'
    cur = conn.cursor()
    cur.execute(sql, (id,))
    conn.commit()

def delete_all_transactions(conn):
    """
    Delete all rows in the transactions table
    :param conn: Connection to the SQLite database
    :return:
    """
    sql = 'DELETE FROM transactions'
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()

def select_all_items(conn):
    """
    Query all rows in the items table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM items")
    rows = cur.fetchall()
    for row in rows:
        print(row)

def select_item_by_code(conn, code):
    """
    Query items by code
    :param conn: the Connection object
    :param priority:
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE item_code=?", (code,))
    rows = cur.fetchall()
    for row in rows:
        print(row)

def select_all_transactions(conn):
    """
    Query all rows in the transactions table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions")
    rows = cur.fetchall()
    for row in rows:
        print(row)

def select_transaction_by_code(conn, code):
    """
    Query transactions by code
    :param conn: the Connection object
    :param priority:
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions WHERE item_code=?", (code,))
    rows = cur.fetchall()
    for row in rows:
        print(row)

if __name__ == '__main__':
    database = 'test_inventory.db'

    create_inventory_tables(database)

    conn = create_connection(database)
    with conn:
        items = [('AA', 'band'), ('BB', 'needle')]
        for item in items:
            create_item(conn, item)

        transactions = [
            ('AA', 'buy', 10, 10, date.today().isoformat()),
            ('BB', 'buy', 10, 10, date.today().isoformat()),
            ('AA', 'buy', 1, 11, date.today().isoformat()),
            ('CC', 'buy', 1, 11, date.today().isoformat()),
            ]
        for transaction in transactions:
            create_transaction(conn, transaction)

        select_all_items(conn)
        select_transaction_by_code(conn, 'DD')
        select_all_transactions(conn)

        delete_all_items(conn)
        delete_all_transactions(conn)
