import os
import logging
from datetime import datetime
from common.singleton import Singleton
from constants import ConfigReader


class Logs(metaclass=Singleton):
    def __init__(self):
        config = ConfigReader()
        self.log_level = config.get_options('Log_Level')
        self.log_output = config.get_options('Log_Output')
        self.output_filename = config.get_options('Log_Output_FileName')
        self.f_log_level = config.get_options('File_Log_Level')
        self.c_log_level = config.get_options('Console_Log_Level')

    def get_logger(self, name):
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        self.init_logger(logger)
        return logger

    def init_logger(self, logger):
        if self.log_output is None:
            return

        if "Console" in self.log_output:
            ch = logging.StreamHandler()
            ch.setFormatter(logging.Formatter('%(levelname)s:%(filename)s:'
                                              '%(lineno)d:%(funcName)s: %(message)s'))
            ch.setLevel(self.c_log_level)
            logger.addHandler(ch)

        if "File" in self.log_output:
            curr_dir = os.getcwd()
            log_dir = os.path.join(curr_dir, '../log')
            os.makedirs(log_dir, exist_ok=True)

            file_name = self.output_filename + str(datetime.now().strftime("%y%m%d_%H%M%S"))
            log_path = os.path.join(log_dir, file_name + '.log')

            fh = logging.FileHandler(log_path)
            fh.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(filename)s:'
                                              '%(lineno)d:%(funcName)s: %(message)s'))
            fh.setLevel(self.f_log_level)
            logger.addHandler(fh)
