CREATE_CATEGORY_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS category(
        category_id SERIAL PRIMARY KEY,
        category_name TEXT NOT NULL,
        UNIQUE(category_name)
    );"""

CREATE_MODALITY_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS modalities(
        modality_id SERIAL PRIMARY KEY,
        active BOOL NOT NULL DEFAULT TRUE,
        modality_name TEXT NOT NULL,
        modality_price INT NOT NULL,
        category_id INT NOT NULL,
        description TEXT,
        FOREIGN KEY (category_id) REFERENCES category(category_id),
        UNIQUE(modality_name)
    );"""

CREATE_PATIENT_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS patients(
        patient_id SERIAL PRIMARY KEY,
        patient_name TEXT NOT NULL,
        patient_emr_id INT,
        patient_gender INT,
        patient_birthdate INT,
    );"""

CREATE_PROVIDER_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS providers(
        provider_id SERIAL PRIMARY KEY,
        provider_name TEXT NOT DATE
    );"""

CREATE_USER_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS users(
        user_id SERIAL PRIMARY KEY,
        user_name TEXT NOT NULL,
        user_password BYTEA NOT NULL,
        UNIQUE(user_name)
    );"""

CREATE_BODY_PART_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS body_parts(
        part_id SERIAL PRIMARY KEY,
        part_name TEXT NOT NULL,
        sub_parts TEXT,
        UNIQUE(part_name)
    );"""

CREATE_SESSION_TABLE = \
    """
    CREATE TABLE IF NOT EXISTS sessions(
        session_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        modality_id INT NOT NULL,
        patient_id INT NOT NULL,
        provider_id INT NOT NULL,
        part_id INT NOT NULL,
        timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        description TEXT,
        FOREIGN KEY (modality_id) REFERENCES modalities(modality_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY (provider_id) REFERENCES providers(provider_id),
        FOREIGN KEY (part_id) REFERENCES body_parts(part_id)
    );"""
