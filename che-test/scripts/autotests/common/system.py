# -*- coding: utf-8; -*-
import functools
from time import time, sleep
import sys
import os
import re
import socket
import inspect
import subprocess

import common.logger as logger
from common.config_module import get_value_from_config


# decorator function to pass file name as argument
def che_autotest(start_file_name):
    # decorator to start and finish the test function
    def internal_decorator(test_suit_function):
        # function to be decorated
        @functools.wraps(test_suit_function)
        def wrapper():
            # Initial setup
            print("")
            test_name = get_test_name(start_file_name)
            test_start_time = time()
            try:
                logger.startTest(test_name)
                logger.info("=" * 80)
                validate_active_configuration()
                logger.info("=" * 80)

                # Main execution
                overall_result = test_suit_function()

                logger.print_empty_line()
            except KeyboardInterrupt:
                logger.finishError("Exception: test '%s' was interrupted by user" % test_name)
                overall_result = False
            except Exception as e:
                logger.finishError("ENVIRONMENT ERROR. Exception within test execution: %s" % e)
                overall_result = False

            # Results output
            logger.info("=" * 80)
            overall_result = (overall_result is None) or overall_result
            if overall_result is None:
                overall_result = True
            if overall_result:
                logger.finishSuccess("Test '%s' overall result" % test_name, test_start_time)
            else:
                logger.finishFail("Test '%s' overall result" % test_name, test_start_time)
        return wrapper
    return internal_decorator


# decorator function to pass file name as argument
def che_test_case(test_case_name=None):
    test_case_name = test_case_name or "Che Test Case"

    # decorator to start and finish the test function
    def internal_decorator(test_case_function):
        # function to be decorated
        @functools.wraps(test_case_function)
        def wrapper(*args, **kwargs):
            logger.start(test_case_name)
            logger.test_case_result = logger.PASS
            test_case_function(*args, **kwargs)
            if logger.test_case_result == logger.PASS:
                return logger.finishSuccess(test_case_name)
            elif logger.test_case_result == logger.FAIL:
                return logger.finishFail(test_case_name)
            else:  # logger.test_case_result == logger.EXPECTED_FAIL
                return logger.finishFailExpected(test_case_name)
        return wrapper
    return internal_decorator


def run_test_and_get_result(test_cases):
    overall_result = True
    tc_passed = 0
    tc_failed = 0
    for case in test_cases:
        test_case_result = case()
        if test_case_result:
            tc_passed += 1
        else:
            tc_failed += 1
        overall_result = test_case_result and overall_result
        logger.print_empty_line()

    logger.info("----------------------------------------")
    logger.info("Test Cases PASSED: %s" % tc_passed)
    logger.info("Test Cases FAILED: %s" % tc_failed)
    return overall_result


def get_test_name(file_handler=None):
    """Get the global test name from current file name

    :param file_handler: current file handler, can also be handler to any file
    """
    return os.path.splitext(os.path.basename(file_handler))[0]


def resolve_domain_names_reachability():
    """Function checks if the domain name for the active configuration are reachable

    :return: True as result of successful validation or assertion
    """
    api_base_url = get_hostname_without_credentials()
    api_host = re.findall("(http://)?([\w\W]*@)?([\w.]*)", api_base_url)[0][2]
    db_host = get_value_from_config("['database']['host']")
    logger.info("Resolving domains names to check their reachability:")
    return resolve_domain("API", api_host) and resolve_domain("DataBase", db_host)


def validate_active_configuration():
    """Function checks if the configuration is correct. The valid configuration value are:

    |---------------|-----------------|--------------------------------|-----------------------|
    | configuration | cfg_environment | api URL                        | DB URL = cfg_dbhost   |
    |---------------|-----------------|--------------------------------|-----------------------|
    | production    | production      | http://api.cherehapa.ru/       | db.aws.che.lo         |
    | vagrant       | development     | http://api.che.test/           | dblocal.che.test      |
    | funk          | staging         | http://api.funk1.cherehapa.ru/ | db.funk1.cherehapa.ru |
    | autofunk      | staging         | http://api.1758.cherehapa.ru/  | db.1758.cherehapa.ru  |
    | testing       | sandbox         | http://api.prntr.cherehapa.ru/ | db.prntr.cherehapa.ru |
    |---------------|-----------------|--------------------------------|-----------------------|

    :return: True as result of successful validation or assertion
    """
    api_base_url = get_hostname_without_credentials()
    api_host = re.findall("([\w\W]*@)?([\w.]*)", api_base_url)[0][1]
    db_host = get_value_from_config("['database']['host']")
    production_db_host = "db.aws.che.lo"
    cfg_environment_name = get_value_from_config("['laravel-api-config']['detectEnvironment']['env']")

    logger.info("Resolving domains names to check their reachability:")
    resolve_domain("API", api_host)
    resolve_domain("DataBase", db_host)

    if cfg_environment_name not in ["production", "development", "staging", "sandbox"]:
        raise Exception("Unexpected environment name in config file")  # wrong configuration, abort
    logger.info("Environment configured for %s server" % cfg_environment_name)
    configuration = {"full_api_domain": api_host,  # full API URL to analyse
                     "expected_api_domain": ".cherehapa.ru",  # expected API domain value
                     "actual_api_domain": re.findall(r'(.[\w]*.[\w]*)$', api_host)[0],  # actual API domain value
                     "full_db_domain": db_host,  # full DataBase URL to analyse
                     "expected_db_domain": ".cherehapa.ru",  # expected DataBase domain value
                     "actual_db_domain": re.findall(r'(.[\w]*.[\w]*)$', db_host)[0]  # actual DataBase domain value
                     }
    additional_domain = False  # logical flag that third level domain analysis is needed to validate the domains of DataBase deployment and API requests

    if cfg_environment_name in ["production"]:  # production configuration
        configuration["expected_db_domain"] = production_db_host
        configuration["actual_db_domain"] = db_host
    if cfg_environment_name in ["development"]:  # vagrant configuration
        configuration["expected_api_domain"] = ".che.test"
        configuration["expected_db_domain"] = ".che.test"
    if cfg_environment_name in ["staging", "sandbox"]:  # staging configuration
        additional_domain = True
    return validate_environment_configuration(configuration, additional_domain)


def resolve_domain(name, domain):
    """Try to resolve the given domain name (hostname)

    :param name: description name of the domain checked (for example "API" or "DataBase")
    :param domain: checked domain string value
    :return: True if domain can be revolved
    """
    try:
        socket.gethostbyname(domain)
        logger.success("%s domain '%s' successfully resolved" % (name, domain))
        return True
    except socket.gaierror:
        logger.error("%s domain '%s' cannot be resolved" % (name, domain))
        return False


def validate_environment_configuration(configuration, additional_domain=False):
    """Validates the API and DataBase domains match expected values and each other

    :param configuration: configuration to be validated
    :param additional_domain: logical flag that third level domain analysis is needed to check the domains of DataBase deployment and API requests
    :return: True if the configuration is valid or exception
    """
    validate_api_domain(configuration["expected_api_domain"], configuration["actual_api_domain"], configuration["full_api_domain"])
    validate_db_domain(configuration["expected_db_domain"], configuration["actual_db_domain"], configuration["full_db_domain"])
    if additional_domain:
        # database additional domain and API additional domain must match each other
        api_server = re.findall(r'([\w]*)(.[\w]*.[\w]*)$', configuration["full_api_domain"])[0][0]
        db_server = re.findall(r'([\w]*)(.[\w]*.[\w]*)$', configuration["full_db_domain"])[0][0]
        validate_additional_domain_for_api_and_db(api_server, db_server)
    logger.print_empty_line()
    return True


def validate_api_domain(expected_api_domain, actual_api_domain, full_api_domain):
    if expected_api_domain != actual_api_domain:
        raise Exception("API domain '%s' doesn't match '%s'" % (full_api_domain, expected_api_domain))
    logger.success("API domain '%s' matches '%s'" % (full_api_domain, expected_api_domain))


def validate_db_domain(expected_db_domain, actual_db_domain, full_db_domain):
    if expected_db_domain != actual_db_domain:
        raise Exception("Database URL '%s' doesn't match '%s'" % (full_db_domain, expected_db_domain))
    logger.success("Database URL '%s' matches '%s'" % (full_db_domain, expected_db_domain))


def validate_additional_domain_for_api_and_db(api_server, db_server):
    if api_server != db_server:
        raise Exception("API server '%s' doesn't match Database server '%s'" % (api_server, db_server))
    logger.success("API server '%s' matches Database server '%s'" % (api_server, db_server))


def wait_and_count(timeout, message=None):
    """Prints message if present and sleeps <timeout> seconds counting seconds down with output to stdout."""
    if message:
        logger.info("Waiting %s seconds for %s.." % (timeout, message))
    for i in range(int(timeout), 0, -1):
        sys.stdout.write("\rTime to wait left: %d " % i)
        sys.stdout.flush()
        sleep(1)
    sys.stdout.write(logger.color.OKGREEN + "\r[%s] [+] Waited for %d seconds: Passed\r\n" % (logger.timestamp(), timeout) + logger.color.ENDC)


def get_hostname_without_credentials():
    hostname = get_value_from_config("['shop']['url']")
    hostname = hostname.strip("/")
    if hostname.find("@"):
        hostname = hostname[hostname.find("@")+1:]
    if hostname.find("www.") < 0:
        hostname = "www." + hostname
    return hostname


def make_target_url():
    target_url = get_value_from_config("['shop']['url']").strip("/")
    account_data = re.findall("(.*[:].*@)", target_url)  # search account data
    if account_data:  # remove existing account data
        target_url = target_url.replace(account_data[0], "")
    if target_url.find("www.") != 0:  # add 'www' prefix
        target_url = "www." + target_url
    if "che.test" in target_url:
        target_url = "http://" + target_url + "/"
    else:
        username = get_value_from_config("['username']", "config/account.json")
        password = get_value_from_config("['password']", "config/account.json")
        target_url = "http://" + username + ":" + password + "@" + target_url + "/"
    return target_url


def function_name():
    return "{name}()".format(name=inspect.stack()[1][3])


def execute_native_shell_command(command, exit_on_error=True):
    if is_tested_host_remote():
        hostname = get_hostname_without_credentials().replace("www.", "")
        username = "root"
        command = "ssh {u}@{h} '{c}'".format(u=username, h=hostname, c=command)
    return execute_shell_command(command, exit_on_error)


def execute_which_in_shell(command, exit_on_error=True):
    # TODO: remove function
    command_result = execute_shell_command("which {0}".format(command), exit_on_error)
    error_message = "Command not found: '{0}'. Check that '{0}' is installed " \
                    "and on $PATH".format(command)
    if not command_result.get("stdout"):
        if exit_on_error:
            raise OSError(error_message)
        return logger.error(error_message)
    return command_result.get("stdout")


def execute_shell_command(command, exit_on_error=True):
    command_result = subprocess.Popen(["/bin/sh", "-c", command],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
    result = {
        "stdout": command_result.stdout.read().decode().strip(),
        "stderr": command_result.stderr.read().decode().strip(),
    }
    if exit_on_error and result.get("stderr"):
        message = "Error while executing {}:\n{}".format(command, result.get("stderr"))
        raise OSError(message)
    return result


def is_tested_host_remote():
    # ------------------------------------------------------------------------
    # env:        gethostname():     config[shop][url]     config[domain]
    # ------------------------------------------------------------------------
    # development www.che.dev        //che.test/           che.test
    # branch      1758               //1758.cherehapa.ru/  1758.cherehapa.ru
    # staging     funk3.cherehapa.ru //funk3.cherehapa.ru/ funk3.cherehapa.ru
    # local       ubuntu             che.test              ---
    # ------------------------------------------------------------------------
    # actual host name for 9-Feb-2018 is equal to 'www.che.dev' in vagrant
    actual_host = socket.gethostname()
    vagrant_hostname = \
        get_value_from_config("['environment']['vagrant_hostname']", "config/env.json")
    if actual_host == vagrant_hostname:
        return False
    if actual_host.find("www.") >= 0:
        actual_host = actual_host[actual_host.find("www.") + 4:]
    config_host = get_value_from_config("['shop']['url']")
    return actual_host not in config_host
