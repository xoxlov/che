# -*- coding: utf-8; -*-
import datetime
import time
import re


PASS = True  # eq.1
FAIL = False  # eq.0
EXPECTED_FAIL = -1
test_case_result = PASS
expected_result = PASS


class color:
    DEFAULT = '\033[0m'
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    SKIPPED = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def timestamp():
    return datetime.datetime.now().strftime("%H:%M:%S")


def start(message):
    print(color.BOLD + "[%s] > %s" % (timestamp(), message) + color.ENDC)


def startTest(test_name):
    start("Starting %s test..." % test_name)


def finishSuccess(message, test_start_time=None):
    print(color.BOLD + color.OKGREEN + "[%s] < [+] %s: PASSED" % (timestamp(), message) + color.ENDC)
    print_execution_time(test_start_time)
    return True


def finishFail(message, test_start_time=None):
    global test_case_result
    print(color.BOLD + color.FAIL + "[%s] < [-] %s: FAILED" % (timestamp(), message) + color.ENDC)
    print_execution_time(test_start_time)
    # Reset test case result for other case.
    test_case_result = PASS
    return False


def finishFailExpected(message, test_start_time=None):
    global test_case_result
    print(color.BOLD + color.FAIL + "[%s] < [#] %s: FAILED (expected)" % (timestamp(), message) + color.ENDC)
    print_execution_time(test_start_time)
    # Reset test case result for other case.
    test_case_result = PASS
    return False


def finishError(message, test_start_time=None):
    print(color.FAIL + "[%s] < [!] %s" % (timestamp(), message) + color.ENDC)
    print_execution_time(test_start_time)
    return False


def finishSkipped(message, test_start_time=None):
    print(color.BOLD + color.SKIPPED + "[%s] < [+] %s: Skipped" % (timestamp(), message) + color.ENDC)
    print_execution_time(test_start_time)


def finishCase(message):
    print(color.BOLD + "[%s] < ---- Finished %s ----" % (timestamp(), message) + color.ENDC)
    print_empty_line()


def print_execution_time(test_start_time=None):
    if test_start_time:
        print(color.BOLD + "Test execution time is %s seconds"
              % (round(time.time() - test_start_time, 1)) + color.ENDC)


def success(message):
    if not re.findall(":[ ]?[Pp]assed", message):
        message += ": Passed"
    print(color.OKGREEN + "[%s] [+] %s" % (timestamp(), message) + color.ENDC)


def fail(message):
    global test_case_result
    if not re.findall(":[ ]?[Ff]ailed", message):
        message += ": Failed"
    signal = ["#", "-"][expected_result]
    message += [" (expected)", ""][expected_result]
    if expected_result == FAIL and (test_case_result == PASS or test_case_result == EXPECTED_FAIL):
        test_case_result = EXPECTED_FAIL
    else:
        test_case_result = FAIL
    print(color.FAIL + "[%s] [%s] %s" % (timestamp(), signal, message) + color.ENDC)


def error(message):
    print(color.FAIL + "[%s] [!] %s" % (timestamp(), message) + color.ENDC)


def info(message):
    print(color.DEFAULT + "[%s] [.] %s" % (timestamp(), message) + color.ENDC)


def debug(message):
    print(color.OKBLUE + "[%s] [.] %s" % (timestamp(), message) + color.ENDC)


def critical(message):
    print(color.FAIL + "[%s] [.] %s" % (timestamp(), message) + color.ENDC)


def warning(message):
    print(color.WARNING + "[%s] [.] %s" % (timestamp(), message) + color.ENDC)


def print_empty_line():
    print("[%s] [.]" % timestamp())
