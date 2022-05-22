from operator import methodcaller


def config_reader():
    with open("config", "r", encoding='utf-8') as fd:
        lines = fd.readlines()
        lines = map(methodcaller("strip"), lines)
        lines = map(methodcaller("split", ";"),
                    filter(lambda l: not l.startswith("#"), lines))
        options = {l[0]: l[1] for l in lines}

    return options
