import logging


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Logs(metaclass=Singleton):
    def get_logger(self, name):
        logger = logging.getLogger(name)
        self.init_logger(logger)
        return logger

    def init_logger(self, logger):
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter('%(levelname)s %(name)s: %(message)s'))
        logger.addHandler(ch)
