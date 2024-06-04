import os
import sys
import logging
import logging.config
import traceback

import yaml

def resource_path(relative_path):
    """ Get the absolute path to a resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Logs():
    def __init__(self):
        # make 'log' directory to store log files
        log_dir = resource_path('../log')
        os.makedirs(log_dir, exist_ok=True)

        # read config file
        try:
            config_file_path = resource_path('./common/log_config.yaml')
            with open(config_file_path, 'rt') as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
                logging.config.dictConfig(config)

            self.err_logger = logging.getLogger("main")
            sys.excepthook = self.handle_exception
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            sys.exit(1)

    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        self.err_logger.error("Unexpected exception",
                              exc_info=(exc_type, exc_value, exc_traceback))
