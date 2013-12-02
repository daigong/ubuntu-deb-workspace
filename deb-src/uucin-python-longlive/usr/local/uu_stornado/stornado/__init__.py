#encoding:utf-8
import os
import logging.config

logging_config_path = os.path.join(os.path.dirname(__file__), 'logging.cfg')
logging.config.fileConfig(logging_config_path)
VERSION = (1, 0, 1, 'alpha', 0)


def get_version():
    return "%d.%d.%d.%s.%d" % VERSION
