import sys
import asyncio
import asyncpg
from asyncpg import UndefinedTableError
from asyncpg import Record
from types import TracebackType
from typing import Optional, Type, List, Tuple, Dict
from PySide6.QtWidgets import QMessageBox
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from common.d_logger import Logs
from constants import ConfigReader

logger = Logs().get_logger("db")


class ConnectPg:
    def __init__(self):
        self.config = ConfigReader()
        self._conn = None

    async def __aenter__(self):
        logger.debug("Trying to connect to db ...")
        logger.debug("Entering context manager, waiting for connection")
        try:
            self._conn = await asyncpg.connect(host=self.config.get_options("Host"),
                                               port=self.config.get_options("Port"),
                                               user=self.config.get_options("User"),
                                               database=self.config.get_options("Database"),
                                               password=self.config.get_options("Password"))
            logger.debug("Successfully connected!!!")
            return self._conn
        except Exception as e:
            logger.debug('Error while connecting to DB')
            logger.debug(e)
            return None

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]):
        logger.debug("Exiting context manager")
        if self._conn:
            logger.debug("Closed connection")
            await self._conn.close()


class DbUtil:

    async def create_tables(self, statements: List[str]):
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

    async def drop_tables(self, table_names: List[str]):
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

    async def select_query(self, query: str, args: List = None):
        """
        Select query
        :param query
        :return: all results if successful, otherwise None
        """
        async with ConnectPg() as conn:
            if conn is None:
                logger.debug("Error while connecting to DB during querying tables")
                return None

            try:
                query = await conn.prepare(query)
                if args:
                    results: List[Record] = await query.fetch(*args)
                else:
                    results: List[Record] = await query.fetch()
                return results
            except Exception as e:
                logger.debug(f'select_query: Error while executing {query}')
                logger.debug(e)
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
        async with ConnectPg() as conn:
            if conn is None:
                logger.debug("Error while connecting to DB during sync_executing")
                return "Connection failed"

            logger.debug("Synchronous executing")
            try:
                results = await conn.executemany(statement, args)
                logger.debug(f"results::\n{results}")
                return results
            except Exception as e:
                logger.debug('executemany: Error during synchronous executing')
                logger.debug(e)
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

        logger.debug("Asynchronous executing")
        config = ConfigReader()
        async with asyncpg.create_pool(host=config.get_options("Host"),
                                       port=config.get_options("Port"),
                                       user=config.get_options("User"),
                                       database=config.get_options("Database"),
                                       password=config.get_options("Password")) as pool:
            queries = [execute(statement, arg, pool) for arg in args]
            results = await asyncio.gather(*queries, return_exceptions=True)
            logger.debug(f":\n{results}")
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
            logger.error(f"args' type{type(args)} must be List[Tuple]")
            return None
        if not isinstance(args[0], Tuple):
            logger.error(f"args element's type{type(args[0])} must be Tuple")
            return None

        stmt = f"DELETE FROM {table} WHERE {col_name} = $1"

        logger.debug(f"Delete rows ...")
        logger.debug(args)

        # results = await self.pool_execute(stmt, args)
        results = await self.executemany(stmt, args)
        logger.debug(f":\n{results}")
        return results


class QtDbUtil:
    def __init__(self):
        self.createConnection()

    def createConnection(self):
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
            QMessageBox.critical(None,
                                 "Error",
                                 f"""<p>The following tables are missing
                                  from the database: {tables}</p>""")
            sys.exit(1)  # Error code 1 - signifies error

    def query_info(self, query_stmt: str) -> Dict:
        """
        query user info with user_name
        """
        logger.debug(query_stmt)

        query = QSqlQuery()
        query.prepare(query_stmt)
        query.exec()

        output_db_record = {}
        if query.next():
            rec = query.record()
            rec_col_count = rec.count()
            for i in range(rec_col_count):
                output_db_record[rec.fieldName(i)] = rec.value(i)
            logger.debug("Got a record!")
            logger.debug(output_db_record)
        else:
            logger.debug("No record found")

        return output_db_record

    def insert_into_db(self,
                       table_name: str,
                       record: Dict):
        """
        Insert input_db_record into DB
        """
        logger.debug(f"Inserting data into {table_name}: {record}")

        def make_stmt(col_names: List, arg_values: List):
            # make a statement like
            # "INSERT INTO tb (f1, f2, f3) VALUES($1, $2, $3)"
            col_part = ','.join(col_names)
            place_holders = []
            i = 1
            for val in arg_values:
                if val == 'DEFAULT':
                    place_holders.append('DEFAULT')
                else:
                    place_holders.append(f'${i}')
                    i += 1
            value_part = ','.join(place_holders)
            stmt = (f"INSERT INTO {table_name} ({col_part})"
                    f" VALUES({value_part})")
            return stmt

        field_names = list(record.keys())
        args = list(record.values())
        stmt = make_stmt(field_names, args)
        logger.debug(f"{stmt} :: {args}")

        query = QSqlQuery()
        query.prepare(stmt)
        for arg in args:
            query.addBindValue(arg)

        if query.exec():
            logger.debug("Data insertion into DB successful!")
        else:
            QMessageBox.warning(None,
                                "Warning",
                                "Improper data to insert !!",
                                QMessageBox.Close)
            logger.debug("Data insertion into DB failed!")
            logger.debug(f"{query.lastError()}")

    def update_db(self,
                  table_name: str,
                  record: Dict,
                  where_clause: str):
        """
        Update DB with input_db_record
        """
        logger.debug(f"Updating data in {table_name}: {record}")

        def make_stmt(record: Dict):
            # make a statement like "UPDATE tb name1 = $1, name2 = $2 WHERE ..."
            place_holders = []
            i = 1
            for name, val in record.items():
                place_holders.append(f'{name} = ${i}')
                i += 1
            stmt_value_part = ','.join(place_holders)
            stmt = f"UPDATE {table_name} SET {stmt_value_part} WHERE {where_clause}"
            return stmt

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
            QMessageBox.warning(None,
                                "Warning",
                                "Improper data to update!!",
                                QMessageBox.Close)
            logger.debug("Data updating failed!")
            logger.debug(f"{query.lastError()}")

    def delete_db(self, table_name: str, where_clause: str):
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
            QMessageBox.warning(None,
                                "Warning",
                                "Improper expression to delete!!",
                                QMessageBox.Close)
            logger.debug("Data deleting failed!")
            logger.debug(f"{query.lastError()}")
