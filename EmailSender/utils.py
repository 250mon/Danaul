from operator import methodcaller


def config_reader(file_name):
    with open(file_name, "r", encoding='utf-8') as fd:
        # strip lines
        lines = map(methodcaller("strip"), fd.readlines())
        # filtering lines starting with '#' or blank lines
        lines_filtered = filter(lambda l: l and not l.startswith("#"), lines)
        # parsing
        lines_dict_iter = map(methodcaller("split", ";"), lines_filtered)
        # converting list to dict
        options = dict(lines_dict_iter)
    return options
