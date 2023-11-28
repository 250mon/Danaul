import asyncio
import pandas as pd
import bcrypt
from db.db_apis import DbApi
from db.db_schema import *


async def insert_initial_data(db_api):

    initial_data = {}

    # initial insert
    initial_data['category'] = pd.DataFrame({
        'category_id': [1, 2],
        'category_name': ['ESWT', 'DOSU']
    })

    initial_data['modalities'] = pd.DataFrame({
        'modality_id': [1, 2],
        'active': [True, True],
        'modality_name': ['ESWT20', 'rESWT30'],
        'modality_price': [60000, 60000],
        'category_id': [1, 1],
    })

    import datetime
    d1 = datetime.date(2000, 9, 10)
    d2 = datetime.date(2012, 1, 30)
    initial_data['patients'] = pd.DataFrame({
        'patient_id': [1, 2],
        'patient_name': ['유비', '관우'],
        'patient_emr_id': [32, 54],
        'patient_gender': ['M', 'M'],
        'patient_birthdate': [d1, d2],
    })

    initial_data['providers'] = pd.DataFrame({
        'provider_id': [1, 2],
        'provider_name': ['Jessie', 'Mike'],
    })

    initial_data['body_parts'] = pd.DataFrame({
        'part_id': [1, 2, 3, 4, 5, 6, 7, 8],
        'part_name': ['Shoulder', 'Elbow', 'Plantar', 'Ankle', 'Wrist',
                      'Cervical', 'Lumbar', 'Thoracic']
    })

    def encrypt_password(password):
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password

    encrypted_pw = encrypt_password('a')
    initial_data['users'] = pd.DataFrame({
        'id': [1, 2],
        'name': ['admin', 'test'],
        'pw': [encrypted_pw, encrypted_pw]
    })

    initial_data['sessions'] = pd.DataFrame({
        'session_id': [1, 2, 3],
        'user_id': [2, 2, 2],
        'modality_id': [1, 2, 1],
        'patient_id': [1, 2, 1],
        'provider_id': [1, 2, 1],
        'part_id': [2, 5, 2],
        'description': ["#1/3", "#1/5", "#2/3"],
        'timestamp': ['DEFAULT', 'DEFAULT', 'DEFAULT'],
        'session_price': [60000, 60000, 60000],
    })

    for table, data_df in initial_data.items():
        # make dataframe for each table
        await db_api.insert_df(table, data_df)

async def main():
    db_api = DbApi()

    # Initialize db by dropping all the tables and then
    # creating them all over again.
    statements = [CREATE_CATEGORY_TABLE,
                  CREATE_MODALITY_TABLE,
                  CREATE_PATIENT_TABLE,
                  CREATE_PROVIDER_TABLE,
                  CREATE_USER_TABLE,
                  CREATE_BODY_PART_TABLE,
                  CREATE_SESSION_TABLE]
    await db_api.initialize_db(statements)

    # After creating the tables, inserting initial data
    await insert_initial_data(db_api)


if __name__ == '__main__':
    asyncio.run(main())
