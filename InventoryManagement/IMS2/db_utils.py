import asyncpg
from operator import methodcaller


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

async def connect_pg():
    options = get_options("db_settings")
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