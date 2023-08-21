import logging
from datetime import datetime
from singleton import Singleton
from constants import ConfigReader, CONFIG_FILE


class Logs(metaclass=Singleton):
    def __init__(self):
        config = ConfigReader(CONFIG_FILE)
        self.log_output = config.get_options('Log_Output')
        self.output_filename = config.get_options('Log_Output_FileName')
        self.f_log_level = self.convert_levels(config.get_options('File_Log_Level'))
        self.c_log_level = self.convert_levels(config.get_options('Console_Log_Level'))

    def get_logger(self, name):
        logger = logging.getLogger(name)
        self.init_logger(logger)
        return logger

    def init_logger(self, logger):
        if "Console" in self.log_output:
            ch = logging.StreamHandler()
            ch.setFormatter(logging.Formatter('%(levelname)s %(name)s: %(message)s'))
            ch.setLevel(self.c_log_level)
            logger.addHandler(ch)

        if "File" in self.log_output:
            output_file_name = self.output_filename + str(datetime.now().strftime("%y%m%d_%H%M%S"))
            fh = logging.FileHandler(output_file_name)
            fh.setFormatter(logging.Formatter('%(levelname)s %(name)s: %(message)s'))
            fh.setLevel(self.f_log_level)
            logger.addHandler(fh)

    def convert_levels(self, str_lvl):
        return getattr(logging, str_lvl)
