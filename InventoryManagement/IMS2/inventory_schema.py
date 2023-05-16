CREATE_CATEGORY_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS category(
        category_id SERIAL PRIMARY KEY,
        category_name TEXT NOT NULL,
        UNIQUE(category_name)
    );"""

CREATE_ITEM_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS item(
        item_id SERIAL PRIMARY KEY,
        item_name TEXT NOT NULL,
        category_id INT NOT NULL,
        FOREIGN KEY (category_id) REFERENCES category(category_id),
        UNIQUE(item_name)
    );"""

CREATE_ITEM_SIZE_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS item_size(
        item_size_id SERIAL PRIMARY KEY,
        item_size VARCHAR ( 20 ) NOT NULL,
        UNIQUE(item_size)
    );"""

CREATE_ITEM_SIDE_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS item_side(
        item_side_id SERIAL PRIMARY KEY,
        item_side VARCHAR ( 20 ) NOT NULL,
        UNIQUE(item_side)
    );"""

CREATE_SKU_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS sku(
        sku_id SERIAL PRIMARY KEY,
        sku_qty INT NOT NULL,
        item_id INT NOT NULL,
        item_size_id INT NOT NULL DEFAULT 1,
        item_side_id INT NOT NULL DEFAULT 1,
        expiration_date DATE NOT NULL DEFAULT '9999-01-01',
        FOREIGN KEY (item_id) REFERENCES item(item_id),
        FOREIGN KEY (item_size_id) REFERENCES item_size(item_size_id),
        FOREIGN KEY (item_side_id) REFERENCES item_side(item_side_id),
        UNIQUE(item_id, item_size_id, item_side_id, expiration_date)
    );"""

CREATE_USER_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS users(
        user_id SERIAL PRIMARY KEY,
        user_name VARCHAR ( 20 ) NOT NULL,
        UNIQUE(user_name)
    );"""

CREATE_TRANSACTION_TYPE_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS transaction_type(
        tr_type_id SERIAL PRIMARY KEY,
        tr_type VARCHAR ( 20 ) NOT NULL
    );"""

CREATE_TRANSACTION_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS transactions(
        tr_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        sku_id INT NOT NULL,
        tr_type_id INT NOT NULL,
        tr_qty INT NOT NULL,
        before_qty INT NOT NULL,
        after_qty INT NOT NULL,
        tr_date DATE NOT NULL DEFAULT CURRENT_DATE,
        FOREIGN KEY (sku_id) REFERENCES sku(sku_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (tr_type_id) REFERENCES transaction_type(tr_type_id)
    );"""
