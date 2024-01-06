import sys
import asyncio
import asyncpg
from asyncpg import UndefinedTableError
from asyncpg import Record
from types import TracebackType
from typing import Optional, Type, List, Tuple, Dict
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from common.d_logger import Logs
from constants import ConfigReader


logger = Logs().get_logger("db")


def make_insert_query(table_name: str,
                      record: Dict):
    # make a statement like
    # "INSERT INTO tb (col1, col2) VALUES($1, $2)"
    def prefix_dollar(i):
        return '$' + str(i)

    # filtering [k1, k2, ... ]
    col_part = [k for k, v in record.items() if v != 'DEFAULT']
    # making value part ['$1', '$2' ...]
    val_part = map(prefix_dollar, range(1, len(col_part) + 1))
    stmt = f"INSERT INTO {table_name} ({','.join(col_part)})" \
           f" VALUES({','.join(val_part)})"
    return stmt


class ConnectPg:
    def __init__(self):
        self.config = ConfigReader()
        self._conn = None

    async def __aenter__(self):
        # logger.debug("Trying to connect to db ...")
        # logger.debug("Entering context manager, waiting for connection")
        try:
            self._conn = await asyncpg.connect(host=self.config.get_options("Host"),
                                               port=self.config.get_options("Port"),
                                               user=self.config.get_options("User"),
                                               database=self.config.get_options("Database"),
                                               password=self.config.get_options("Password"))
            # logger.debug("Successfully connected!!!")
            return self._conn
        except Exception as e:
            logger.debug('Error while connecting to DB')
            logger.debug(e)
            return None

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]):
        # logger.debug("Exiting context manager")
        if self._conn:
            # logger.debug("Closed connection")
            await self._conn.close()


class DbUtil:

    @staticmethod
    async def create_tables(statements: List[str]):
        """
        Create tables
        sync_execute can be used instead.
        :param statements: sql statments
        :return:
        """
        results = []
        async with ConnectPg() as conn:
            if conn is None:
                logger.debug("Error while connecting to DB during creating tables")
                return

            logger.info("Creating the tables")
            for statement in statements:
                try:
                    logger.info(f"{statement}")
                    status = await conn.execute(statement)
                    results.append(status)
                    logger.info(status)
                except Exception as e:
                    logger.info(f'create_tables: Error while creating table: {statement}')
                    logger.info(e)
            logger.info("Finished creating the tables")
        return results

    @staticmethod
    async def drop_tables(table_names: List[str]):
        """
        Remove the tables
        :param table_names:
        :return:  the list of results of dropping the tables or
                  None if connection fails
        """
        results = []
        async with ConnectPg() as conn:
            if conn is None:
                logger.debug("Error while connecting to DB during removing tables")
                return None

            logger.info("Removing the tables")
            for table in table_names:
                try:
                    sql_stmt = f'DROP TABLE {table} CASCADE;'
                    result = await conn.execute(sql_stmt)
                    results.append(result)
                except UndefinedTableError as ute:
                    logger.info('drop_table: Trying to drop an undefined table', ute)
                except Exception as e:
                    logger.info('drop_table: Error while dropping tables')
                    logger.info(e)
            logger.info("Finished removing the tables")
        return results

    @staticmethod
    async def select_query(query_stmt: str, args: List = None):
        """
        Select query
        :param query_stmt
        :return: all results if successful, otherwise None
        """
        async with ConnectPg() as conn:
            if conn is None:
                logger.debug("Error while connecting to DB during querying tables")
                return None

            try:
                query_stmt = await conn.prepare(query_stmt)
                if args:
                    results: List[Record] = await query_stmt.fetch(*args)
                else:
                    results: List[Record] = await query_stmt.fetch()
                return results
            except Exception as e:
                logger.debug(f'select_query: Error while executing {query_stmt}')
                logger.debug(e)
                return None

    @staticmethod
    async def executemany(query_stmt: str, args: List[Tuple]):
        """
        Execute a query through connection.executemany()
        :param query_stmt: query to execute
        :param args: list of arguments which are supplied to the query one by one
        :return:
            if successful, None
            otherwise, exception or string
        """
        async with ConnectPg() as conn:
            if conn is None:
                logger.debug("Error while connecting to DB during sync_executing")
                return "Connection failed"

            logger.debug("Synchronous executing")
            try:
                results = await conn.executemany(query_stmt, args)
                logger.debug(f"results::\n{results}")
                return results
            except Exception as e:
                logger.debug('executemany: Error during synchronous executing')
                logger.debug(e)
                return e

    @staticmethod
    async def pool_execute(query_stmt: str, args: List[Tuple]):
        """
        Execute a query through ascynpg.pool
        :param query_stmt: query to execute
        :param args: list of arguments which are supplied to the query one by one
        :return:
            if successful, list of results of queries
            otherwise, exception
        """

        async def execute(stmt, arg, _pool):
            async with _pool.acquire() as conn:
                logger.debug(stmt)
                logger.debug(arg)
                return await conn.execute(stmt, *arg)

        logger.debug("Asynchronous executing")
        config = ConfigReader()
        async with asyncpg.create_pool(host=config.get_options("Host"),
                                       port=config.get_options("Port"),
                                       user=config.get_options("User"),
                                       database=config.get_options("Database"),
                                       password=config.get_options("Password")) as pool:
            queries = [execute(query_stmt, arg, pool) for arg in args]
            results = await asyncio.gather(*queries, return_exceptions=True)
            logger.debug(f":\n{results}")
            return results

    @staticmethod
    async def delete(table, col_name, args: List[Tuple]):
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
            logger.error(f"args' type{type(args)} must be List[Tuple]")
            return None
        if not isinstance(args[0], Tuple):
            logger.error(f"args element's type{type(args[0])} must be Tuple")
            return None

        stmt = f"DELETE FROM {table} WHERE {col_name} = $1"

        logger.debug(f"Delete rows ...")
        logger.debug(args)

        # results = await self.pool_execute(stmt, args)
        results = await DbUtil.executemany(stmt, args)
        logger.debug(f":\n{results}")
        return results


class QtDbUtil:
    def __init__(self):
        self.createConnection()

    @staticmethod
    def createConnection():
        """Set up the connection to the database.
        Check for the tables needed."""
        config = ConfigReader()
        database = QSqlDatabase.addDatabase("QPSQL")
        database.setHostName(config.get_options("Host"))
        database.setPort(int(config.get_options("Port")))
        database.setUserName(config.get_options("User"))
        database.setPassword(config.get_options("Password"))
        database.setDatabaseName(config.get_options("Database"))
        if not database.open():
            logger.error("Unable to Connect.")
            logger.error(database.lastError())
            sys.exit(1)  # Error code 1 - signifies error
        else:
            logger.debug("Connected")

        # Check if the tables we need exist in the database
        # tables_needed = {"users"}
        # tables_not_found = tables_needed - set(database.tables())
        # if tables_not_found:
        tables = database.tables()
        if "users" not in tables:
            logger.debug(f"The following tables are missing from"
                         f" the database: {tables}")
            sys.exit(1)  # Error code 1 - signifies error

    @staticmethod
    def query(query_stmt: str) -> Dict[str, List]:
        """
        query
        """
        logger.debug(query_stmt)

        query = QSqlQuery()
        query.prepare(query_stmt)
        query.exec()

        field_names = list()
        values = list()
        while query.next():
            rec = query.record()
            col_count = rec.count()
            # field_names part
            if len(field_names) == 0:
                field_names = [rec.fieldName(i) for i in range(col_count)]
                logger.debug('<<Field Names>>')
                logger.debug(field_names)

            # values part
            rec_values = [rec.value(i) for i in range(col_count)]
            values.append(rec_values)

        logger.debug('<<Values>>')
        logger.debug(values)

        return {'field_names': field_names, 'values': values}

    @staticmethod
    def insert_into_db(table_name: str, record: Dict):
        """
        Insert input_db_record into DB
        """
        logger.debug(f"Inserting data into {table_name}: {record}")

        args = list(record.values())
        stmt = make_insert_query(table_name, record)
        logger.debug(f"{stmt} :: {args}")

        query = QSqlQuery()
        query.prepare(stmt)
        for arg in args:
            query.addBindValue(arg)

        if query.exec():
            logger.debug("Data insertion into DB successful!")
        else:
            logger.debug("Data insertion into DB failed!")
            logger.debug(f"{query.lastError()}")

    @staticmethod
    def update_db(table_name: str, record: Dict, where_clause: str):
        """
        Update DB with input_db_record
        """
        logger.debug(f"Updating data in {table_name}: {record}")

        def make_stmt(_record: Dict):
            # make a statement like "UPDATE tb name1 = $1, name2 = $2 WHERE ..."
            place_holders = []
            i = 1
            for name, val in _record.items():
                place_holders.append(f'{name} = ${i}')
                i += 1
            stmt_value_part = ','.join(place_holders)
            _stmt = f"UPDATE {table_name} SET {stmt_value_part} WHERE {where_clause}"
            return _stmt

        args = list(record.values())
        stmt = make_stmt(record)
        logger.debug(f"{stmt} :: {args}")

        query = QSqlQuery()
        query.prepare(stmt)
        for arg in args:
            query.addBindValue(arg)

        if query.exec():
            logger.debug("Data updating successful!")
        else:
            logger.debug("Data updating failed!")
            logger.debug(f"{query.lastError()}")

    @staticmethod
    def delete_db(table_name: str, where_clause: str):
        """
        Delete a record in DB
        """
        logger.debug(f"Deleting data in {table_name} where {where_clause}")
        query = QSqlQuery()
        stmt = f"DELETE FROM {table_name} WHERE {where_clause}"
        query.prepare(stmt)

        if query.exec():
            logger.debug("Data deleting successful!")
        else:
            logger.debug("Data deleting failed!")
            logger.debug(f"{query.lastError()}")
