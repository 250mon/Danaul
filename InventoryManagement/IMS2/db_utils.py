import asyncio
import asyncpg
from asyncpg import UndefinedTableError
from asyncpg import Record
from operator import methodcaller
from types import TracebackType
from typing import Optional, Type, List, Tuple
from di_logger import Logs
import logging

logger = Logs().get_logger('db_utils')
logger.setLevel(logging.DEBUG)


class DbConfig:
    def __init__(self, config_file):
        options = self.get_options(config_file)
        self.host = options['host']
        self.port = options['port']
        self.user = options['user']
        self.database = options['database']
        self.passwd = options['password']

    def get_options(self, file_path="config"):
        try:
            with open(file_path, 'r') as fd:
                # strip lines
                lines = map(methodcaller("strip"), fd.readlines())
                # filtering lines starting with '#' or blank lines
                lines_filtered = filter(lambda l: l and not l.startswith("#"), lines)
                # parsing
                words_iter = map(methodcaller("split", "="), lines_filtered)
                # converting map obj to dict
                options = {k.strip(): v.strip() for k, v in words_iter}

        except Exception as e:
            print(e)
            exit(0)

        return options


async def connect_pg(db_config_file):
    config_options = DbConfig(db_config_file)
    try:
        conn = await asyncpg.connect(host=config_options.host,
                                     port=config_options.port,
                                     user=config_options.user,
                                     database=config_options.database,
                                     password=config_options.passwd)
        return conn
    except Exception as e:
        logger.exception('Error while connecting to DB', e)
        raise e



class ConnectPg:
    def __init__(self, db_config_file):
        config_options = DbConfig(db_config_file)
        self.host = config_options.host
        self.port = config_options.port
        self.user = config_options.user
        self.database = config_options.database
        self.passwd = config_options.passwd

        self._conn = None

    async def __aenter__(self):
        logger.debug('Trying to connect to db ...')
        logger.debug('Entering context manager, waiting for connection')
        try:
            self._conn = await asyncpg.connect(host=self.host,
                                               port=self.port,
                                               user=self.user,
                                               database=self.database,
                                               password=self.passwd)
            logger.debug('Successfully connected!!!')
            return self._conn
        except Exception as e:
            logger.exception('Error while connecting to DB', e)
            return None

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]):
        logger.debug('Exiting context manager')
        if self._conn:
            logger.debug('Closed connection')
            await self._conn.close()


class DbUtil:
    def __init__(self, db_config_file: str):
        self.db_config_file = db_config_file

    async def create_tables(self, statements: List[str]):
        """
        Create tables
        sync_execute can be used instead.
        :param statements: sql statments
        :return:
        """
        results = []
        async with ConnectPg(self.db_config_file) as conn:
            if conn is None:
                logger.debug('create_tables: Error while connecting to DB during creating tables')
                return

            logger.info('create_tables: Creating the tables')
            for statement in statements:
                try:
                    logger.info(f'{statement}')
                    status = await conn.execute(statement)
                    results.append(status)
                    logger.debug(status)
                except Exception as e:
                    logger.exception(f'create_tables: Error while creating table: {statement}', e)
            logger.info('create_tables: Finished creating the tables')
        return results

    async def drop_tables(self, table_names: List[str]):
        """
        Remove the tables
        :param table_names:
        :return:  the list of results of dropping the tables or
                  None if connection fails
        """
        results = []
        async with ConnectPg(self.db_config_file) as conn:
            if conn is None:
                logger.debug('drop_table: Error while connecting to DB during removing tables')
                return None

            logger.info('drop_table: Removing the tables')
            for table in table_names:
                try:
                    sql_stmt = f'DROP TABLE {table} CASCADE;'
                    result = await conn.execute(sql_stmt)
                    results.append(result)
                except UndefinedTableError as ute:
                    logger.exception('drop_table: Trying to drop an undefined table', ute)
                except Exception as e:
                    logger.exception('drop_table: Error while dropping tables', e)
        logger.info('drop_table: Finished removing the tables')
        return results

    async def select_query(self, query: str, args: List = None):
        """
        Select query
        :param query
        :return: all results if successful, otherwise None
        """
        async with ConnectPg(self.db_config_file) as conn:
            if conn is None:
                logger.debug('select_query: Error while connecting to DB during querying tables')
                return None

            try:
                query = await conn.prepare(query)
                if args:
                    results: List[Record] = await query.fetch(*args)
                else:
                    results: List[Record] = await query.fetch()
                return results
            except Exception as e:
                logger.exception(f'select_query: Error while executing {query}', e)
                return None


    async def executemany(self, statement: str, args: List[Tuple]):
        """
        Execute a statement through connection.executemany()
        :param statement: statement to execute
        :param args: list of arguments which are supplied to the statement one by one
        :return:
            if successful, None
            otherwise, exception or string
        """
        async with ConnectPg(self.db_config_file) as conn:
            if conn is None:
                logger.debug('executemany: Error while connecting to DB during sync_executing')
                return "Connection failed"

            logger.info('executemany: Synchronous executing')
            try:
                results = await conn.executemany(statement, args)
                logger.info(f'executemany: results::\n{results}')
                return results
            except Exception as e:
                logger.exception('executemany: Error during synchronous executing', e)
                return e


    async def pool_execute(self, statement: str, args: List[Tuple]):
        """
        Execute a statement through ascynpg.pool
        :param statement: statement to execute
        :param args: list of argements which are supplied to the statement one by one
        :return:
            if successful, list of results of queries
            otherwise, exception
        """
        async def execute(stmt, arg, pool):
            async with pool.acquire() as conn:
                logger.debug(stmt)
                logger.debug(arg)
                return await conn.execute(stmt, *arg)

        logger.info('pool_execute: Asynchronous executing')
        config_options = DbConfig(self.db_config_file)
        async with asyncpg.create_pool(host=config_options.host,
                                       port=config_options.port,
                                       user=config_options.user,
                                       database=config_options.database,
                                       password=config_options.passwd) as pool:
            queries = [execute(statement, arg, pool) for arg in args]
            results = await asyncio.gather(*queries, return_exceptions=True)
            logger.debug(f'pool_execute: results::\n{results}')
            return results

    async def delete(self, table, col_name, args: List[Tuple]):
        """
        Delete rows where col value is in the args list from table
        :param table: table name
        :param col_name: column name to check
        :param args: argments to search for
        :return:
            When using executemany,
                if successful, None
                otherwise, exception or string
            When using pool_execute,
                if successful, list of results of queries
                otherwise, exception
        """
        if not isinstance(args, List):
            logger.error(f"delete: args' type{type(args)} must be List[Tuple]")
            return None
        if not isinstance(args[0], Tuple):
            logger.error(f"delete: args element's type{type(args[0])} must be Tuple")
            return None

        stmt = f"DELETE FROM {table} WHERE {col_name} = $1"

        logger.debug(f'delete: Delete rows ...')
        logger.debug(args)

        # results = await self.pool_execute(stmt, args)
        results = await self.executemany(stmt, args)
        logger.debug(f'delete: results::\n{results}')
        return results
