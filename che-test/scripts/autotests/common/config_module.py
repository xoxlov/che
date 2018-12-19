# -*- coding: utf-8; -*-
import re
import os
import json
import common.logger as logger


def load(file=None):
    """Tries to load the configuration from predefined config file, if failed then fail message printed and script aborted

    :return: handler to the default config file
    """
    common_config = get_dir_by_suffix("che-config/common.json")
    local_config = get_dir_by_suffix("che-test/scripts/autotests/config.json")
    if file:
        config_file = file
    elif os.path.exists(common_config):
        config_file = common_config
    else:
        config_file = local_config

    try:
        file_handler = open(config_file, "r")
        config = json.load(file_handler)
        return config
    except IOError:
        logger.error("Cannot access configuration file '%s'" % config_file)
        raise
    except ValueError:
        logger.error("Error while loading data: bad json in file '%s'" % config_file)
        raise


def get_value_from_config(value_to_get="", file=None):
    """Read value from default config, value can be set either using list of sections or with directly set path

    :param value_to_get: section path in config of requested value
    :param file:
    :return: value of requested parameter in default config
    """
    config = load(file)
    if isinstance(value_to_get, list):  # like list ['host', 'url']
        parameter_name = "config[" + "][".join(value_to_get) + "]"
    elif isinstance(value_to_get, str):  # like string "['host']['url']"
        parameter_name = "config" + value_to_get
    else:
        parameter_name = "config[" + value_to_get + "]"
    try:
        return eval(parameter_name)
    except KeyError as e:
        logger.error("Cannot evaluate parameter %s from %s" % (e, value_to_get))
        raise


def get_dir_by_suffix(suffix):
    if str(os.getcwd()).find("/che-all") >= 0:  # deployed environment
        up_count = re.search("(.*/)(che-all.*)", os.getcwd()).group(2).count("/")
    else:  # local environment
        up_count = re.search("(.*/)(var/www.*)", os.getcwd()).group(2).count("/") - 1
    return os.path.abspath(os.path.join("../" * up_count, suffix))
