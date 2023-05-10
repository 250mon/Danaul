import asyncpg
from operator import methodcaller
from types import TracebackType
from typing import Optional, Type


def get_options(file_path="config"):
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

async def connect_pg(db_settings):
    options = get_options(db_settings)
    host_url = options['host']
    port = options['port']
    user = options['user']
    database = options['database']
    passwd = options['password']

    connection = await asyncpg.connect(host=host_url,
                                       port=port,
                                       user=user,
                                       database=database,
                                       password=passwd)
    return connection


class ConnectPG:
    def __init__(self, db_settings):
        self._connection = None
        self.db_settings = db_settings

    async def __aenter__(self):
        print('Entering context manager, waiting for connection')

        options = get_options(self.db_settings)
        host_url = options['host']
        port = options['port']
        user = options['user']
        database = options['database']
        passwd = options['password']

        self._connection = await asyncpg.connect(host=host_url,
                                                 port=port,
                                                 user=user,
                                                 database=database,
                                                 password=passwd)

        return self._connection

    async def __aexit__(self,
                        exc_type: Optional[Type[BaseException]],
                        exc_val: Optional[BaseException],
                        exc_tb: Optional[TracebackType]):
        print('Exiting context manager')
        await self._connection.close()
        print('Closed connection')