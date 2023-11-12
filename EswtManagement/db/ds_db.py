import os
import asyncio
import pandas as pd
import bcrypt
from typing import List
from constants import ConfigReader
from db.db_utils import DbUtil
from db.db_schema import *
from common.d_logger import Logs, logging


class TreatmentsDb:
    def __init__(self):
        self.logger = Logs().get_logger(os.path.basename(__file__))

        self.db_util = DbUtil()

    async def create_tables(self):
        self.logger.info("Creating tables ...")
        statements = [CREATE_CATEGORY_TABLE,
                      CREATE_TREATMENT_TABLE,
                      CREATE_PROVIDER_TABLE,
                      CREATE_USER_TABLE,
                      CREATE_SESSION_TABLE]
        return await self.db_util.create_tables(statements)

    async def drop_tables(self):
        table_names = ['category', 'treatments', 'providers', 'users',
                       'sessions']
        # dropping is always in a reverse order from creating
        return await self.db_util.drop_tables(table_names[::-1])

    async def initialize_db(self):
        await self.drop_tables()
        await self.create_tables()

    async def insert_df(self, table: str, df: pd.DataFrame):
        def make_stmt(table_name: str, row_values: List):
            place_holders = []
            i = 1
            for val in row_values:
                if val == 'DEFAULT':
                    place_holders.append('DEFAULT')
                else:
                    place_holders.append(f'${i}')
                    i += 1
            stmt_value_part = ','.join(place_holders)
            stmt = f"INSERT INTO {table_name} VALUES({stmt_value_part})"
            return stmt
        self.logger.debug(f"Insert into {table}...")
        self.logger.debug(f"\n{df}")
        args = df.values.tolist()
        stmt = make_stmt(table, args[0])

        # we need to remove 'DEFAULT' from args
        non_default_df = df.loc[:, df.iloc[0, :] != 'DEFAULT']
        args = non_default_df.values.tolist()

        self.logger.debug(f"{stmt} {args}")
        # return await self.db_util.pool_execute(stmt, args)
        return await self.db_util.executemany(stmt, args)

    async def upsert_treatments_df(self, treatments_df: pd.DataFrame):
        """
        Insert treatments_df into DB, if the treatment_name pre-exists, update it
        :param treatments_df:
        :return:
        """
        stmt = """INSERT INTO treatments VALUES(DEFAULT, $1, $2, $3, $4)
                    ON CONFLICT (treatment_name)
                    DO
                     UPDATE SET active = $1,
                                treatment_name = $2,
                                category_id = $3,
                                description = $4"""
        args = [(tx.active, tx.treatment_name, tx.category_id, tx.description)
                for tx in treatments_df.itertuples()]

        self.logger.debug("Upsert treatments ...")
        self.logger.debug(args)
        return await self.db_util.executemany(stmt, args)

    async def delete_df(self, table: str, del_df: pd.DataFrame):
        col_name, id_series = next(del_df.treatments())
        args = [(_id,) for _id in id_series]
        self.logger.debug(f"Delete {col_name} = {args} from {table} ...")
        return await self.db_util.delete(table, col_name, args)

    async def update_df(self, table: str, up_df: pd.DataFrame):
        col_names = up_df.columns
        id_name = col_names[0]
        place_holders = [f'{col_name}=${i}'for i, col_name in enumerate(col_names[1:], start=2)]
        ph_str = ','.join(place_holders)
        stmt = f"UPDATE {table} SET {ph_str} WHERE {id_name}=$1"
        args = [_tuple[1:] for _tuple in up_df.itertuples()]
        self.logger.debug(f"{stmt}")
        self.logger.debug(args)
        return await self.db_util.executemany(stmt, args)

    async def update_sessions_df(self, sessions_df: pd.DataFrame):
        """
        Update sessions in DB from trs_df based on session_id
        :param trs:
        :return:
        """
        stmt = """UPDATE sessions SET treatment_id = $2,
                                      treatment_detail = $3
                                      provider_id = $4,
                                      timestamp = $5,
                                      description = $6
                                   WHERE session_id = $1"""
        args = [(session.session_id, session.treatment_id, session.treatment_detail,
                 session.provider_id, session.timestamp, session.description)
                for session in sessions_df.itertuples()]
        self.logger.debug("Update sessions ...")
        self.logger.debug(args)
        return await self.db_util.executemany(stmt, args)

    async def delete_sessions_df(self, sessions_df: pd.DataFrame):
        args = [(session_row.session_id,) for session_row in sessions_df.itertuples()]
        self.logger.debug(f"Delete ids {args} from sessions table ...")
        return await self.db_util.delete('sessions', 'session_id', args)

async def main():
    danaul_db = TreatmentsDb()

    # Initialize db by dropping all the tables and then
    # creating them all over again.
    # After creating the tables, inserting initial data
    async def initialize():
        await danaul_db.initialize_db()
        return

        extra_data = {}
        # initial insert
        extra_data['category'] = pd.DataFrame({
            'id': [1, 2],
            'name': ['ESWT', '도수치료']
        })

        extra_data['providers'] = pd.DataFrame({
            'id': [1],
            'name': ['김정은']
        })

        def encrypt_password(password):
            # Generate a salt and hash the password
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed_password

        encrypted_pw = encrypt_password('a')
        extra_data['users'] = pd.DataFrame({
            'id': [1, 2],
            'name': ['admin', 'test'],
            'pw': [encrypted_pw, encrypted_pw]
        })

        for table, data_df in extra_data.items():
            # make dataframe for each table
            await danaul_db.insert_df(table, data_df)

    async def insert_treatments():
        treatments_df = pd.DataFrame({
            'treatment_id': ['DEFAULT', 'DEFAULT'],
            'active': [True, True],
            'treatment_name': ['ESWT20', 'ESWT30'],
            'category_id': [1, 1],
            'description': ['', '']
        })
        print(await danaul_db.insert_df('treatments', treatments_df))

    async def insert_sessions():
        # Inserting sessions
        sessions_df = pd.DataFrame({
            'session_id': ['DEFAULT'],
            'treatment_id': [0],
            'treatment_detail': ['trapezius'],
            'provider_id': [0],
            'timestamp': ['DEFAULT'],
            'description': ['']
        })
        print(await danaul_db.insert_df('sessions', sessions_df))

    await initialize()
    # await insert_treatments()
    # await insert_sessions()


if __name__ == '__main__':
    ConfigReader().read_config_file('../ds_config')
    asyncio.run(main())
