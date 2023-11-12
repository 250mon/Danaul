import os
import asyncio
import asyncpg
from asyncpg import UndefinedTableError
from asyncpg import Record
from types import TracebackType
from typing import Optional, Type, List, Tuple
from common.d_logger import Logs
from constants import ConfigReader


class ConnectPg:
    def __init__(self, config):
        self.config = config
        self._conn = None

    async def __aenter__(self):
        try:
            self._conn = await asyncpg.connect(host=self.config.get_options("Host"),
                                               port=self.config.get_options("Port"),
                                               user=self.config.get_options("User"),
                                               database=self.config.get_options("Database"),
                                               password=self.config.get_options("Password"))
            return self._conn
        except Exception as e:
            raise e

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]):
        if self._conn:
            await self._conn.close()


class DbUtil:
    def __init__(self):
        self.logger = Logs().get_logger(os.path.basename(__file__))
        self.config = ConfigReader()

    async def create_tables(self, statements: List[str]):
        """
        Create tables
        sync_execute can be used instead.
        :param statements: sql statments
        :return:
        """
        self.logger.debug("Creating tables")
        results = []
        try:
            async with ConnectPg(self.config) as conn:
                for statement in statements:
                    try:
                        self.logger.info(f"{statement}")
                        status = await conn.execute(statement)
                        results.append(status)
                        self.logger.debug(status)
                    except Exception as e:
                        self.logger.error(f'create_tables: Error while creating table: {statement}', e)
                self.logger.info("Tables created")
        except Exception as e:
            self.logger.error(e)

        return results

    async def drop_tables(self, table_names: List[str]):
        """
        Remove the tables
        :param table_names:
        :return:  the list of results of dropping the tables or
                  None if connection fails
        """
        self.logger.debug(f"Dropping tables {table_names}")
        results = []
        try:
            async with ConnectPg(self.config) as conn:
                for table in table_names:
                    try:
                        sql_stmt = f'DROP TABLE {table} CASCADE;'
                        result = await conn.execute(sql_stmt)
                        results.append(result)
                    except UndefinedTableError as ute:
                        self.logger.error('drop_table: Trying to drop an undefined table', ute)
                    except Exception as e:
                        self.logger.error('drop_table: Error while dropping tables', e)
            self.logger.info("Tables removed")
        except Exception as e:
            self.logger.error(e)

        return results

    async def select_query(self, query: str, args: List = None):
        """
        Select query
        :param query
        :return: all results if successful, otherwise None
        """
        results = []
        try:
            async with ConnectPg(self.config) as conn:
                try:
                    query = await conn.prepare(query)
                    if args:
                        results: List[Record] = await query.fetch(*args)
                    else:
                        results: List[Record] = await query.fetch()
                except Exception as e:
                    self.logger.error(f'select_query: Error while executing {query}', e)
        except Exception as e:
            self.logger.error(e)

        return results

    async def executemany(self, statement: str, args: List[Tuple]):
        """
        Execute a statement through connection.executemany()
        :param statement: statement to execute
        :param args: list of arguments which are supplied to the statement one by one
        :return:
            if successful, None
            otherwise, exception or string
        """
        results = None
        self.logger.debug(f"executemany({statement}, {args})")

        try:
            async with ConnectPg(self.config) as conn:
                self.logger.debug("Synchronous executing")
                try:
                    results = await conn.executemany(statement, args)
                    self.logger.debug(f"results::\n{results}")
                except Exception as e:
                    results = e
                    self.logger.error('executemany: Failed synchronous executing')
        except Exception as e:
            self.logger.error(e)

        return results

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
                self.logger.debug(stmt)
                self.logger.debug(arg)
                return await conn.execute(stmt, *arg)

        self.logger.debug("Asynchronous executing")
        results = []
        try:
            async with asyncpg.create_pool(host=self.config.get_options("Host"),
                                           port=self.config.get_options("Port"),
                                           user=self.config.get_options("User"),
                                           database=self.config.get_options("Database"),
                                           password=self.config.get_options("Password")) as pool:
                queries = [execute(statement, arg, pool) for arg in args]
                results = await asyncio.gather(*queries, return_exceptions=True)
                self.logger.debug(f":\n{results}")
        except Exception as e:
            self.logger.error(e)

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
            self.logger.error(f"args' type{type(args)} must be List[Tuple]")
            return None
        if not isinstance(args[0], Tuple):
            self.logger.error(f"args element's type{type(args[0])} must be Tuple")
            return None

        stmt = f"DELETE FROM {table} WHERE {col_name} = $1"

        self.logger.debug(f"Delete rows ...")
        self.logger.debug(args)

        results = await self.executemany(stmt, args)
        self.logger.debug(f":\n{results}")
        return results
