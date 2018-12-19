# -*- coding: utf-8; -*-
import common.logger as logger


def is_equal(actual_value, expected_value, value_name, fail_info_message=None):
    """Function checks if actual_value is equal to expected_value
    and outputs result, if result is False then fail_message is printed.

    :param actual_value:
    :param expected_value:
    :param value_name:
    :param fail_info_message:
    :return: boolean result of examination
    """
    result = (actual_value == expected_value)
    if result:
        logger.success("Verify %s: %s (test EQ: actual %s, expected %s)" % (value_name, "Passed", actual_value, expected_value))
    else:
        logger.fail("Verify %s: %s (test EQ: actual %s, expected %s)" % (value_name, "Failed", actual_value, expected_value))
        if fail_info_message:
            logger.fail(fail_info_message)
    return result


def is_not_equal(actual_value, expected_value, value_name, fail_message=None):
    """function checks if actual_value is NOT equal to expected_value and outputs result, if result is False then fail_message is printed

    :param actual_value: value to be compared
    :param expected_value: value to be compared
    :param value_name: name or description of value to be verified;
    :param fail_message: additional message for failed result, if no fail_message set
                         then it has value of None and failed result is not printed
    :return: boolean result of examination
    """
    result = (actual_value != expected_value)
    if result:
        logger.success("Verify %s: %s (test NE: actual %s, expected %s)" % (value_name, "Passed", actual_value, expected_value))
    else:
        logger.fail("Verify %s: %s (test NE: actual %s, expected %s)" % (value_name, "Failed", actual_value, expected_value))
        if fail_message:
            logger.fail(fail_message)
    return result


def print_test_case_result(test_case_result, name):
    """Function receive result of Test Case execution, prints if it has passed or failed

    :param test_case_result: result of test case execution
    :param name: test case identificator
    :return: boolean result of Test Case execution
    """
    if test_case_result:
        logger.finishSuccess("TestCase '%s'" % name)
    else:
        logger.finishFail("TestCase '%s'" % name)
    return test_case_result


def print_test_suit_result(passed, failed):
    """Function prints amount of passed and failed test cases after test execution

    :param passed: amount of passed test cases
    :param failed: amount of failed test cases
    :return: None
    """
    logger.info("----------------------------------------")
    logger.info("Test Cases PASSED: %s" % passed)
    logger.info("Test Cases FAILED: %s" % failed)
