#!/usr/bin/env python3
# -*- coding: utf-8; -*-
import time
import urllib.parse
import random
import re

import common.logger as logger
from common.system import che_autotest, che_test_case, run_test_and_get_result
from common.json_functions import validate_json_schema, validate_json_by_schema
from common.config_module import get_value_from_config
from common.randomize import get_random_string
from common.injections import get_sql_injection_strings, is_sql_injection_successful_by_user
from common.request import send_http_request


###############################################################################
# Settings and schemas
###############################################################################
cfg_request_key = get_value_from_config("['key']", "config/aviasales.json")
cfg_request_partner_id = get_value_from_config("['partner_id']", "config/aviasales.json")
cfg_request_interval = get_value_from_config("['interval']", "config/aviasales.json")
cfg_request_base_url = "http:" + get_value_from_config("[u'api'][u'url']").replace("/v2", "/v1") + "/aviaSalesResult.json"

# username used in SQL injection attempts
glob_userlength = random.choice([8, 12, 15, 30, 50])
glob_user2inject = get_random_string(size=glob_userlength)


###############################################################################
# Functions
###############################################################################
def config_str_to_period(configstr, strname):
    """Parse the string value of configuration parameter that determines the time
     period used in request, config value can take values like '5h', '5d', '5m',
     '5y' or 'XXdd', where XX - any integer number, dd - one char time period code.

    :param configstr: string value of configuration parameter for used period of time
    :param strname: name of configuration parameter, cannot be empty
    :return: the amount of seconds for the time period defined by config parameter
    """
    # values used for response data validation, Xh/Xd/Xm/Xy assumed as cfg_request_interval value, where X - any digit
    units2period = {'h': 3600, 'd': 86400, 'm': 2592000, 'y': 31536000}
    period = re.findall("(\d[\d]?)([hdmy])", configstr)  # result is like [('51', 'd')]
    if len(period) != 1:
        raise AssertionError("Error configuration value of '%s' = '%s'" % (strname, configstr))
    # calculate the returned period
    return int(period[0][0]) * units2period[period[0][1]]


###############################################################################
# Functions implementing Test Cases
###############################################################################
@che_test_case("Aviasales request injection with sql injection values as additional key in request")
def test_request_injection_as_parameter():
    """Send the requests to API with injection values as additional parameter of
    the query. If the query is processed ignoring injection parameter the function
    returns True, if not - the function returns False.
    """
    # requests for injection attempts will be stored in array
    request_url = []

    # compute time period to be used in loop
    request_interval = config_str_to_period(cfg_request_interval, "cfg_request_interval")

    # create injections data to pass as additional not expected parameter
    injections = get_sql_injection_strings(get_random_string(size=2), glob_user2inject)
    # Replace special characters in string for every item in injections
    for index, item in enumerate(injections):
        injections[index] = urllib.parse.quote(item)
    # create a set of requests to be used for injection - injection string are placed in the beginning
    for injection_string in injections:
        request_url.append(cfg_request_base_url + '?' + injection_string + '&key=' + cfg_request_key + \
                           '&partner=' + cfg_request_partner_id + \
                           '&interval=' + cfg_request_interval + \
                           '&timestamp=')
    logger.info("%s attempts will be used for injections as parameters" % len(request_url))

    function_result = True
    # injections in additional paramater (unused by API, i.e. unexpected for it)
    for count, request in enumerate(request_url):
        iteration_name = "Parameter injection request #%d" % (count + 1)
        logger.print_empty_line()
        logger.info(iteration_name)

        # time limitations needed for response validation
        time_current = int(time.time())
        time_limit_req = time_current - request_interval
        if time_limit_req < time_current - config_str_to_period(cfg_request_interval, "cfg_request_interval") / 2:
            time_limit_req = time_current - config_str_to_period(cfg_request_interval, "cfg_request_interval") / 2
        # time_limit is set between timelimit from config and current date-time
        time_limit = str(time_current - config_str_to_period(cfg_request_interval, "cfg_request_interval") // 2)

        request = request + time_limit
        resp = send_http_request(request, "get")

        # the response is obtained anyway, so prepare it for processing
        response = resp.json()
        # analyse the response
        if resp.status_code == 200:
            # Since we got correct response code we have to check the schema used for json data
            logger.success("Response code is equal to 200")
            # the schema should be validated first
            function_result = \
                validate_json_by_schema(response, "aviasales_response_with_success_schema") \
                and function_result
            try:
                # the data received should be validated next
                success = True
                if not response:  # server responce is empty - it's ok, but have to report about it
                    logger.info("Response data is empty")
                for item in response:
                    # check that dates are within the requested period
                    time_sample = int(time.mktime(time.strptime(item['updated_at'], "%d.%m.%Y %H:%M:%S")))
                    if time_limit_req > time_sample or time_current < time_sample:
                        logger.fail("Date/time validation error while checking json reply: %s is out of range" % item['updated_at'])
                        logger.info("Object: %s" % item)
                        success = False
                        function_result = False
                        logger.fail("Stop of data validation: an invalid data chunk found, other chunks (if any) will be left unchecked.")
                        break
                if success:
                    logger.success("Dates from response validated successfully")
            # in case of any validation error the exception is thrown
            except Exception as e:
                logger.fail("Data validation error when checking JSON reply from parameter injection request")
                logger.info("Exception: %s" % e)
                raise Exception("Exception due to response for parameter injection request is incorrect")

        else:  # resp.status_code != 200
            function_result = False
            logger.fail("Got unexpected response code %s while injection" % resp.status_code)
            logger.info("URL: %s" % request)
            logger.info("Injection: %s" % urllib.parse.unquote(injections[count]))
            validate_json_by_schema(response, "aviasales_response_with_error_schema")
            continue

    # check that user was not created and no injection happened
    function_result = not is_sql_injection_successful_by_user(glob_user2inject) and function_result
    return function_result


@che_test_case("Aviasales request injection with direct injection in request")
def test_request_injection():
    """Send the requests to API with injection values intruded into parameters of the query
    Returns True if no injection was detected, otherwise False
    """
    # time_limit is set to the current date and time minus 10 days
    time_limit = str(int(time.time()) - (86400 * 10))

    # create a set of requests to be used for injection, requests for injection attempts will be stored in array
    request_url = []
    # injection into request_key
    injections = get_sql_injection_strings(cfg_request_key, glob_user2inject)
    for index, item in enumerate(injections):
        injections[index] = urllib.parse.quote(item)
        single_request = cfg_request_base_url + '?' + 'key=' + injections[index] + \
                         '&partner=' + cfg_request_partner_id + \
                         '&interval=' + cfg_request_interval + \
                         '&timestamp=' + time_limit
        request_url.append(single_request)
    # injection into partner_id
    injections = get_sql_injection_strings(cfg_request_partner_id, glob_user2inject)
    for index, item in enumerate(injections):
        injections[index] = urllib.parse.quote(item)
        single_request = cfg_request_base_url + '?' + 'key=' + cfg_request_key + \
                         '&partner=' + injections[index] + \
                         '&interval=' + cfg_request_interval + \
                         '&timestamp=' + time_limit
        request_url.append(single_request)
    # injection into interval
    injections = get_sql_injection_strings(cfg_request_interval, glob_user2inject)
    for index, item in enumerate(injections):
        injections[index] = urllib.parse.quote(item)
        single_request = cfg_request_base_url + '?' + 'key=' + cfg_request_key + \
                         '&partner=' + cfg_request_partner_id + \
                         '&interval=' + injections[index] + \
                         '&timestamp=' + time_limit
        request_url.append(single_request)
    # injection into timestamp
    injections = get_sql_injection_strings(time_limit, glob_user2inject)
    for index, item in enumerate(injections):
        injections[index] = urllib.parse.quote(item)
        single_request = cfg_request_base_url + '?' + 'key=' + cfg_request_key + \
                         '&partner=' + cfg_request_partner_id + \
                         '&interval=' + cfg_request_interval + \
                         '&timestamp=' + injections[index]
        request_url.append(single_request)

    length = len(request_url)  # variable will be used for current injection output
    logger.info("%s attempts will be used for injections attempts" % str(length))

    # injections in additional parameter (unused by API, i.e. unexpected for it)
    function_result = True
    for count, request in enumerate(request_url):
        iteration_name = "Injection request #%d" % (count + 1)
        logger.print_empty_line()
        logger.info(iteration_name)
        # try to send request and get the response back
        resp = send_http_request(request, "get")

        # analyse the response
        if resp.status_code != 200:
            schema_name = "aviasales_response_with_error_schema"
        else:  # resp.status_code = 200
            schema_name = "aviasales_response_with_success_schema"
        # check the schema
        schema_result = \
            validate_json_by_schema(resp.json(), schema_name,
                                    abort_on_exception=True)
        function_result = function_result and schema_result
        if schema_result:
            logger.success("Response schema was checked successfully")
        else:
            logger.fail("Error while checking response schema '%s'" % schema_name)
        logger.info("URL: %s" % request)

    # check that user was not created and no injection happened
    function_result = not is_sql_injection_successful_by_user(glob_user2inject) and function_result
    return function_result


###############################################################################
# main function definition
###############################################################################
@che_autotest(__file__)
def test_aviasales_report_check_injections():
    """Test suite to verify the tickets API for injections in requests
    """
    result = \
        validate_json_schema("aviasales_response_with_success_schema") \
        and validate_json_schema("aviasales_response_with_error_schema") \
        and validate_json_schema("api_error_without_description")
    logger.print_empty_line()
    test_cases = [
        test_request_injection_as_parameter,
        test_request_injection
    ]
    return run_test_and_get_result(test_cases) and result


if __name__ == '__main__':
    test_aviasales_report_check_injections()
