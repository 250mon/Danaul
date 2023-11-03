CREATE_CATEGORY_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS category(
        category_id SERIAL PRIMARY KEY,
        category_name TEXT NOT NULL,
        UNIQUE(category_name)
    );"""

CREATE_TREATMENT_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS treatments(
        treatment_id SERIAL PRIMARY KEY,
        active BOOL NOT NULL DEFAULT TRUE,
        treatment_name TEXT NOT NULL,
        category_id INT NOT NULL,
        description TEXT,
        FOREIGN KEY (category_id) REFERENCES category(category_id),
        UNIQUE(treatment_name)
    );"""

CREATE_PROVIDER_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS providers(
        provider_id SERIAL PRIMARY KEY,
        provider_name TEXT NOT NULL,
    );"""

CREATE_USER_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS users(
        user_id SERIAL PRIMARY KEY,
        user_name TEXT NOT NULL,
        user_password BYTEA NOT NULL,
        UNIQUE(user_name)
    );"""

CREATE_SESSIONS_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS sessions(
        session_id SERIAL PRIMARY KEY,
        treatment_id INT NOT NULL,
        treatment_detail TEXT,
        provider_id INT NOT NULL,
        timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        description TEXT,
        FOREIGN KEY (treatment_id) REFERENCES treatments(treatment_id),
        FOREIGN KEY (provider_id) REFERENCES providers(provider_id)
    );"""
