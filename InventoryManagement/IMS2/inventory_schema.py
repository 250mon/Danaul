CREATE_CATEGORY_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS category(
    category_id SERIAL PRIMARY KEY,
    category_name TEXT NOT NULL
    );"""

CREATE_ITEM_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS item(
    item_id SERIAL PRIMARY KEY,
    item_name TEXT NOT NULL,
    category_id INT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES category(category_id)
    );"""

CREATE_ITEM_SIZE_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS item_size(
    item_size_id SERIAL PRIMARY KEY,
    item_size_name TEXT NOT NULL
    );"""

CREATE_ITEM_SIDE_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS item_side(
    item_side_id SERIAL PRIMARY KEY,
    item_side_name TEXT NOT NULL
    );"""

CREATE_SKU_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS sku(
    sku_id SERIAL PRIMARY KEY,
    sku_quantity INT NOT NULL,
    item_id INT NOT NULL,
    item_size_id INT,
    item_side_id INT,
    expiration_date DATE,
    FOREIGN KEY (item_id) REFERENCES item(item_id),
    FOREIGN KEY (item_size_id) REFERENCES item_size(item_size_id),
    FOREIGN KEY (item_side_id) REFERENCES item_side(item_side_id)
    );"""

CREATE_USER_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS user(
    user_id SERIAL PRIMARY KEY,
    user_name TEXT NOT NULL
    );"""

CREATE_TRANSACTION_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS transaction(
    tr_id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    sku_id INT NOT NULL,
    tr_quantity INT NOT NULL,
    tr_date DATE NOT NULL DEFAULT CURRENT_DATE,
    FOREIGN KEY (sku_id) REFERENCES sku(sku_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id),
    );"""

SIDE_INSERT = \
    """
    INSERT INTO item_side VALUES(1, 'Right');
    INSERT INTO item_side VALUES(2, 'Left');
    """

SIZE_INSERT = \
    """
    INSERT INTO item_size VALUES(1, 'Small');
    INSERT INTO item_size VALUES(2, 'Medium');
    INSERT INTO item_size VALUES(3, 'Large');
    INSERT INTO item_size VALUES(4, '40cc');
    INSERT INTO item_size VALUES(5, '120cc');
    """

USER_INSERT = \
    """
    INSERT INTO item_size VALUES(1, 'admin');
    INSERT INTO item_size VALUES(2, 'test');
    """