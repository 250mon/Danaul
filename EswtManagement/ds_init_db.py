import asyncio
import pandas as pd
from db.db_apis import DbApi
from db.db_schema import *
from common.auth_util import encrypt_password


async def insert_initial_data(db_api):

    initial_data = {}

    # initial insert
    initial_data['category'] = pd.DataFrame({
        'category_name': ['ESWT', 'DOSU']
    })

    initial_data['modalities'] = pd.DataFrame({
        'active': [True, True],
        'modality_name': ['ESWT20', 'rESWT30'],
        'modality_price': [60000, 60000],
        'category_id': [1, 1],
    })

    initial_data['patients'] = pd.DataFrame({
        'patient_emr_id': [3, 54],
        'patient_name': ['유비', '관우'],
        'patient_gender': ['M', 'M'],
    })

    encrypted_pw = encrypt_password('a')
    initial_data['users'] = pd.DataFrame({
        'active': [True, True],
        'user_name': ['admin', 'test'],
        'user_password': [encrypted_pw, encrypted_pw],
        'user_realname': ['jj', 'tt'],
        'user_job': ['진료', '물리치료']
    })

    initial_data['body_parts'] = pd.DataFrame({
        'part_name': ['Shoulder', 'Elbow', 'Plantar',
                      'Ankle', 'Wrist', 'Cervical',
                      'Lumbar', 'Thoracic']
    })

    initial_data['sessions'] = pd.DataFrame({
        'user_id': [1, 1, 1],
        'modality_id': [1, 2, 1],
        'patient_id': [1, 1, 2],
        'provider_id': [2, 2, 2],
        'part_id': [4, 7, 3],
        'description': ["#1/3", "#1/5", "#2/3"],
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
                  CREATE_USER_TABLE,
                  CREATE_BODY_PART_TABLE,
                  CREATE_SESSION_TABLE]
    await db_api.initialize_db(statements)

    # After creating the tables, inserting initial data
    await insert_initial_data(db_api)


if __name__ == '__main__':
    asyncio.run(main())
