import asyncpg
from operator import methodcaller
from types import TracebackType
from typing import Optional, Type
import logging


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
        logging.exception('Error while connecting to DB', e)
        raise e



class ConnectPG:
    def __init__(self, db_config_file):
        config_options = DbConfig(db_config_file)
        self.host = config_options.host
        self.port = config_options.port
        self.user = config_options.user
        self.database = config_options.database
        self.passwd = config_options.passwd

        self._conn = None

    async def __aenter__(self):
        logging.debug('Entering context manager, waiting for connection')


        try:
            self._conn = await asyncpg.connect(host=self.host,
                                               port=self.port,
                                               user=self.user,
                                               database=self.database,
                                               password=self.passwd)
            return self._conn
        except Exception as e:
            logging.exception('Error while connecting to DB', e)
            return None

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]):
        logging.debug('Exiting context manager')
        if self._conn:
            logging.debug('Closed connection')
            await self._conn.close()