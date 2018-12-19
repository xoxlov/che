#!/usr/bin/env python3
# -*- coding: utf-8; -*-
import datetime
import time
from dateutil.relativedelta import relativedelta
import urllib.parse

import common.logger as logger
from common.database import CheDb
from common.system import che_autotest, che_test_case, function_name
from common.system import run_test_and_get_result
from common.json_functions import validate_json_schema
import random
from common.config_module import get_value_from_config
from common.request import send_request_api_partner


###############################################################################
# Config values, Constants and Globals
###############################################################################
cfg_request_key = get_value_from_config("['key']", "config/aviasales.json")
cfg_request_partner_id = get_value_from_config("['partner_id']", "config/aviasales.json")
cfg_request_base_url = "http:" + get_value_from_config("[u'api'][u'url']").replace("/v2", "/v1") + "/aviaSalesResult.json"


###############################################################################
# Functions used in Test Cases
###############################################################################
def timestamp_plus_days(time_stamp, delta_days):
    return int(time_stamp + datetime.timedelta(days=delta_days).total_seconds())


def create_random_timestamp_inside_interval(left_days_delta, right_days_delta, current_time=time.time()):
    assert left_days_delta < right_days_delta
    left_border_interval = timestamp_plus_days(current_time, left_days_delta)
    right_border_interval = timestamp_plus_days(current_time, right_days_delta)
    point_inside = random.randint(left_border_interval, right_border_interval)
    return point_inside


def calc_parameters_for_request(rel_data=None):
    """Calculate common parameters of aviasales API request to be used in output and data validation

    :param rel_data: relative date from current date to calculate the moment-in-past value
    :return: cortege of values for aviasales API requests and data validation
    """
    if rel_data is None:
        rel_data = relativedelta()
    date_now = datetime.datetime.now()  # current moment date and time time
    date_past = date_now - rel_data  # specified period ago from current moment
    time_current = int(time.mktime(date_now.timetuple()))  # numeric timestamp for current moment
    time_stamp = int(time.mktime(date_past.timetuple()))  # numeric timestamp for date in past
    timeline = "(%s - %s)" % (date_past.__format__("%d.%m.%Y %H:%M:%S"), date_now.__format__("%d.%m.%Y %H:%M:%S"))
    return date_now, date_past, time_current, time_stamp, timeline


def calc_parameters_for_custom_interval(interval_left, interval_right):
    """Calculate timestamp values for intervals test cases, result is returned as list in format
    [{"value":timestamp, "description":string}]

    :param interval_left: left time border of the interval
    :param interval_right: right time border of the interval
    :return: list of values [{"value":timestamp, "description":string}]
    """
    DAYS_TO_INTERVAL = 30
    time_current = int(time.mktime(datetime.datetime.now().timetuple()))  # numeric timestamp for current moment
    timestamps = [
        {"value": int(interval_left - datetime.timedelta(days=DAYS_TO_INTERVAL).total_seconds()), "description": "timestamp is very long before interval"},
        {"value": int(interval_left - 1), "description": "timestamp is one second before interval"},
        {"value": int(interval_left), "description": "timestamp is at the start of interval"},
        {"value": int((interval_left + interval_right) // 2), "description": "timestamp is inside of interval"},
        {"value": int(interval_right), "description": "timestamp is at the end of interval"},
        {"value": int(interval_right + 1), "description": "timestamp is second later than interval"},
        {"value": int((interval_right + time_current) // 2), "description": "timestamp is later than interval"},
        {"value": "", "description": "timestamp is empty"},
        {"value": "  ", "description": "timestamp is made of spaces"},
        {"value": None, "description": "timestamp is missing"},
    ]
    return timestamps


def format_intervals_for_testcase(interval_left, interval_right):
    """Format interval to printable string and make test case name using formatted interval

    :param interval_left: left time border of the interval
    :param interval_right: right time border of the interval
    :return: set of values ("request_interval": string, "tc_name": string)
    """
    request_interval = "%s-%s" % (
        datetime.datetime.strftime(datetime.datetime.fromtimestamp(interval_left), "%d.%m.%Y %H:%M:%S"),
        datetime.datetime.strftime(datetime.datetime.fromtimestamp(interval_right), "%d.%m.%Y %H:%M:%S"))
    tc_name = "custom interval from past to present (%s)" % request_interval
    return request_interval, tc_name


def construct_aviasales_request(values=None, special=None):
    """Construct the aviasales api request with given parameters.

    :param values: dictionary with data correspond the parameters list for aviasales api request
    :param special: marker for special request
    :return: string that represents the aviasales api request with given parameters
    """
    if values and not isinstance(values, dict):
        raise ValueError("%s: incorrect function use, no valid parameter ('values') given" % function_name())
    DAYS_AMOUNT_DEFAULT = 5
    INTERVAL_DEFAULT = "%sd" % DAYS_AMOUNT_DEFAULT
    TIMESTAMP_DEFAULT = str(int(time.time() - datetime.timedelta(days=DAYS_AMOUNT_DEFAULT).total_seconds()))

    # set default values
    http = cfg_request_base_url
    params = {"key": cfg_request_key,
              "partner": cfg_request_partner_id,
              "interval": "default",
              "timestamp": "default",
              "status": None}
    # key may be already in quoted format, so fix it
    params["key"] = urllib.parse.unquote(params["key"])
    # proceed special cases first
    if special == "request_without_parameters":
        return http
    if special == "request_with_key_only":
        return http + "?" + urllib.parse.urlencode({"key": params["key"]})
    # 'special' value cannot be arbitrary
    if special:
        raise ValueError("%s: incorrect use of 'special' parameter (value different from '%s' expected)"
                         % (function_name(), special))

    if "http" in values.keys():
        http = values["http"]
        values.pop("http")
    # replace default values in the parameters dict
    for item in values:
        if item not in params.keys():
            logger.warning("%s: parameter '%s' cannot be evaluated as request parameter, skipped"
                           % (function_name(), item))
            continue
        params[item] = str(values[item])

    if params["interval"] == "default":
        params["interval"] = str(INTERVAL_DEFAULT)
    if params["timestamp"] == "default":
        params["timestamp"] = str(TIMESTAMP_DEFAULT)

    # clear the dict from missing values
    params = {key: params[key] for key in params if params[key] not in [None, "None"]}

    # return full URL
    request = http + "?" + '&'.join(["%s=%s" % (key, urllib.parse.quote(params[key])) for key in params.keys()])
    return request


def fail_message(policy_id, actual_value, expected_value, value_name):
    """Print message for variable if actual value is not equal to expected
    """
    logger.fail("Verify '%s' for policy '%s': Failed (test EQ: actual '%s', expected '%s')" % (value_name, policy_id, actual_value, expected_value))


def get_alternative_partner_id():
    """Send request to the DB to get partner ID different from aviasales ID

    :return: correct partner ID different from aviasales ID
    """
    query = "select affiliateId from partners where affiliateId != " + cfg_request_partner_id + " order by rand() limit 1;"
    result = CheDb().execute_query(query)
    if result:
        alternative_partner_id = result[0][0]
        logger.success("Alternative 'Partner ID' generated: %s ('partners.affiliateId' is different from aviasales value)" % alternative_partner_id)
        return alternative_partner_id
    raise ValueError("Alternative 'Partner ID' generation error: cannot get from DB 'affiliateId' different from aviasales")


def get_not_existing_partner_id():
    """Generate value of Partner ID that doesn't exist in database

    :return: correct partner ID that doesn't exist in database
    """
    query = "select max(affiliateId) + 1 from partners where affiliateId is not null;"
    result = CheDb().execute_query(query)
    if result:
        partner_absent_value = result[0][0]
        logger.success("Not existing 'Partner ID' generated: %s (no such 'partners.affiliateId' value)" % partner_absent_value)
        return partner_absent_value
    raise ValueError("Not existing 'Partner ID' generation error: cannot get any partner different from aviasales")


def get_alternative_valid_keys():
    """Send request to the DB to get list of apiKeys.keys different from configuration value cfg_request_key.
    Note: all available keys should be tested to make sure the result is same for every key.

    :return: correct access key different from aviasales key taken from configuration value cfg_request_key
    """
    keys = CheDb().get_valid_partner_keys()
    if keys:
        alternative_valid_keys = list(x for x in keys if x != cfg_request_key)
        logger.success("Alternative 'API Key' generated: %s values ('apiKeys.key' is different from configuration value)" % len(alternative_valid_keys))
        return alternative_valid_keys
    raise ValueError("Alternative 'API Key' generation error: cannot get any valid 'apiKeys.key' different from configuration value")


def validate_data_from_response(req_url, response, description, left_date=None, right_date=None, status_expected=None):
    """Validate data for every record from response: policy record in database, policy date, policy status are checked to be correct.

    :param req_url: URL the request was made
    :param response: response to be validated
    :param description: string description of aviasales request
    :param timestamp left_date: optional, left border of the time line allowed
    :param timestamp right_date: optional, rigth border of the time line allowed
    :param string status_expected: optional, expected status of the policy record
    :return: True if all data is ok, False if some data is wrong
    """
    if not response:  # server responce is empty - it's ok, but have to report about it
        logger.success("Verify data for request '%s': Passed (empty)" % description)
        return True
    # response is not empty
    success_records = verify_policies_are_correct_in_db(response, description)
    success_dates = verify_date_is_correct_in_db(response, left_date, right_date, description)
    success_status = True
    if status_expected is not None:
        success_status = verify_status_is_correct_in_db(response, status_expected, description)
    function_result = success_records and success_dates and success_status
    if not function_result:
        logger.info("URL: %s" % req_url)
    return function_result


def verify_policies_are_correct_in_db(policies_array, description):
    success_records = True
    with CheDb() as db_conn:
        for record in policies_array:
            data_exist_in_db = verify_policy_id_in_db(db_conn, record['policy_id']) \
                               and verify_currency_in_db(db_conn, record['policy_id'], record['currency']) \
                               and verify_updated_at_in_db(db_conn, record['policy_id'], record['updated_at']) \
                               and verify_description_in_db(db_conn, record['policy_id'], record['description']) \
                               and verify_status_in_db(db_conn, record['policy_id'], record['status']) \
                               and verify_profit_in_db(db_conn, record['policy_id'], record['profit']) \
                               and verify_price_in_db(db_conn, record['policy_id'], record['price']) \
                               and verify_marker_in_db(db_conn, record['policy_id'], record['marker'])
            if not data_exist_in_db:
                success_records = False
    if success_records:
        logger.success("Verify Aviasales request '%s', records data in database validated successfully" % description)
        return True
    else:
        logger.fail("Verify Aviasales request '%s', records data in database validated successfully" % description)
        return False


def verify_policy_id_in_db(db_conn, policy_id):
    """Check if the policy with given ID exists in the single copy

    :param db_conn:
    :param policy_id: value to be checked, in database = policies.id
    :return: True if policy exists, False otherwise
    """
    query = "select id from policies where id=%s;" % policy_id
    query_result = db_conn.execute_query(query)
    is_not_single = (len(query_result) != 1)
    if is_not_single:
        fail_message(policy_id, query_result, [policy_id], "policy_id")
        return False
    return True


def verify_currency_in_db(db_conn, policy_id, currency):
    """Check if the currency for given policy is correct

    :param db_conn:
    :param policy_id: policy id for checked query
    :param currency: value to be checked, value currency: 'rub' (always)
    :return: True if the currency is ok
    """
    query = "select currency from basket where product_id=%s;" % policy_id
    query_result = db_conn.execute_query(query)
    is_not_single = (len(query_result) != 1)
    if is_not_single:
        fail_message(policy_id, query_result, [str(currency).upper()], "Currency")
        return False
    has_incorrect_value = (str(query_result[0][0]).upper() != str(currency).upper())
    if has_incorrect_value:
        fail_message(policy_id, str(query_result[0][0]).upper(), str(currency).upper(), "Currency")
        return False
    return True


def verify_updated_at_in_db(db_conn, policy_id, updated_at):
    """Check if the updated_at for given policy is correct

    :param db_conn:
    :param policy_id: value to be checked, in database = policies.id
    :param updated_at: value to be checked, in database = policies.dateUpdated
    :return: True if the 'updated_at' is ok
    """
    query = "select dateUpdated from policies where id=%s;" % policy_id
    query_result = db_conn.execute_query(query)
    is_not_single = (len(query_result) != 1)
    if is_not_single:
        fail_message(policy_id, query_result, [updated_at], "Updated_at")
        return False
    updated_at_database = query_result[0][0].strftime("%d.%m.%Y %H:%M:%S")
    has_incorrect_value = (updated_at_database != updated_at)
    if has_incorrect_value:
        fail_message(policy_id, updated_at_database, updated_at, "Updated_at")
        return False
    return True


def verify_description_in_db(db_conn, policy_id, description):
    """Check if the description for given policy is correct.
    The value of policies.code can be empty, so to avoid any exception while processing this field:
     - first send query to check if the policies.code exists in database
     - if policies.code is not NULL then verify the description

    :param db_conn:
    :param policy_id: value to be checked, in database = policies.id
    :param description: value to be checked, constructed by API from database as "Туристическая страховка (<policies.code>)"
    :return: True if the 'description' is ok
    """
    query1 = "select COUNT(code) from policies where id=%s;" % policy_id
    query2 = "select code from policies where id=%s;" % policy_id

    query_result = db_conn.execute_query(query1)
    if not query_result:
        fail_message(policy_id, query_result, [1], "COUNT(policies.code)")
        return False  # no data found for query1
    # Note: API constructs descriptions on the fly, variable description_constructed contains descriptions
    #   constructed depending on DB with algorithm API expected to follow
    description_count = query_result[0][0]
    # if counting query returned no data, i.e. no significant value of policies.code is available (equal to NULL),
    #   the value of description from database is not appended with any additional data
    if description_count == 0:
        description_constructed = u'Туристическая страховка ()'
    # if the code field is not NULL then make query and get the policies.code to create description_database
    else:
        query_result = db_conn.execute_query(query2)
        is_not_single = (len(query_result) != 1)
        if is_not_single:
            fail_message(policy_id, query_result, [], "Description:policies.code")
            return False
        description_constructed = u"Туристическая страховка (%s)" % query_result[0][0]
    # now verify the description and return the result
    has_incorrect_value = (description_constructed != description)
    if has_incorrect_value:
        fail_message(policy_id, description_constructed.encode('utf-8'), description.encode('utf-8'), "Description")
        return False
    return True


def verify_status_in_db(db_conn, policy_id, status):
    """Check if the status for given policy is correct. Value of 'status' is calculated:
     - status = canceled: policies.dateCancelled IS NOT NULL
     - status = paid: <policies.id> -> <basket.productId> -> <basket.orderId> -> <saleOrder.id> -> saleOrder.payed == Y
     - status = processing: all other cases

    :param db_conn:
    :param policy_id: value to be checked, in database = policies.id
    :param status: value to be checked, value = canceled | processing | paid
    :return: True if the 'status' is ok
    """
    statuses_dict = {
        "canceled": {
            "query": "select COUNT(dateCancelled) from policies where id=%s;" % policy_id,
            "expected_data": "1"},
        "paid": {
            "query": "select payed from saleOrder where id=(select orderId from basket where productId=(select id from policies where id=%s));" % policy_id,
            "expected_data": "Y"}
    }
    default_status_value = "processing"

    for status_key in statuses_dict:
        # get the data and verify it is correct
        query_result = db_conn.execute_query(statuses_dict[status_key]["query"])
        # check if data is valid
        is_not_single = (len(query_result) != 1)
        if is_not_single:
            logger.fail("Verify 'Status' for policy '%s': Failed (invalid data when executing query to mySQL)" % policy_id)
            logger.fail("Query: %s" % statuses_dict[status_key]["query"])
            return False
        # if found correct status - check corresponding data
        if status_key == status:
            value_from_database = query_result[0][0]
            has_incorrect_value = (str(value_from_database) != statuses_dict[status]["expected_data"])
            if has_incorrect_value:
                fail_message(policy_id, value_from_database, statuses_dict[status]["expected_data"], "Status '%s'" % status)
                return False
            return True
    # if not returned from function then continue with default status value - check if the database status of the policy is default status value
    has_incorrect_value = (status != default_status_value)
    if has_incorrect_value:
        fail_message(policy_id, status, default_status_value, "Status")
        return False
    return True


def verify_profit_in_db(db_conn, policy_id, profit):
    """Checks if the profit for given policy is correct

    :param db_conn:
    :param policy_id: value to be checked, in database = policies.id
    :param profit: value to be checked, in database = <policies.calculationId> -> <calculations.id> -> (calculations.price * calculations.feeRate)
    :return: True if the 'profit' is ok
    """
    query = "select calculations.price*calculations.feeRate from calculations where id = (select calculationId from policies where id=%s);" % policy_id
    query_result = db_conn.execute_query(query)

    is_not_single = (len(query_result) != 1)
    if is_not_single:
        fail_message(policy_id, query_result, [profit], "Profit")
        return False
    profit_database = round(query_result[0][0], 2)
    limit_round = 0.0101  # rounding inaccuracy for profit calculations, digits 3-4 are needed for correct floating point operation
    has_incorrect_value = (abs(profit_database - profit) > limit_round)
    if has_incorrect_value:
        fail_message(policy_id, profit_database, profit, "Profit")
        return False
    return True


def verify_price_in_db(db_conn, policy_id, price):
    """Check if the price for given policy is correct

    :param db_conn:
    :param policy_id: value to be checked, in database = policies.id
    :param price: value to be checked, in database = <policies.calculationId> -> <calculations.id> -> calculations.price
    :return: True if the 'price' is ok
    """
    query = "select calculations.price from calculations where id = (select calculationId from policies where id=%s);" % policy_id
    query_result = db_conn.execute_query(query)

    is_not_single = (len(query_result) != 1)
    if is_not_single:
        fail_message(policy_id, query_result, [str(price)], "Price")
        return False

    price_database = float(query_result[0][0])
    limit_round = 0.0501  # rounding inaccuracy for profit calculations, digits 3-4 are needed for correct floating point operation
    has_incorrect_value = (abs(price_database - price) > limit_round)
    if has_incorrect_value:
        fail_message(policy_id, str(price_database), str(price), "Price")
        return False
    return True


def verify_marker_in_db(db_conn, policy_id, marker):
    """Check if the marker for given policy is correct

    :param db_conn:
    :param policy_id: value to be checked, in database = policies.id
    :param marker: value to be checked, in database = <policies.id> -> <basket.productId> -> <basket.orderId> ->
                                                                       <saleOrder.id> -> saleOrder.trackingNumber
    :return: True if the 'marker' is ok
    """
    query = "select trackingNumber from saleOrder where id=(select orderId from basket where productId=(select id from policies where id=%s));" % policy_id
    query_result = db_conn.execute_query(query)

    is_not_single = (len(query_result) != 1)
    if is_not_single:
        fail_message(policy_id, query_result, [str(marker)], "Marker")
        return False

    marker_database = query_result[0][0]
    has_incorrect_value = (marker_database != marker)
    if has_incorrect_value:
        fail_message(policy_id, str(marker_database), str(marker), "Marker")
        return False
    return True


def verify_date_is_correct_in_db(policies_array, left_date, right_date, description):
    success_dates = True
    for policy_data in policies_array:
        # verify that dates are inside of interval selected
        time_from_record = time.mktime(time.strptime(policy_data['updated_at'], "%d.%m.%Y %H:%M:%S"))
        if (left_date and left_date > time_from_record) or (right_date and right_date < time_from_record):
            logger.fail("Date/time validation error while checking json reply: %s is out of range" % policy_data['updated_at'])
            success_dates = False
    if success_dates and (left_date or right_date):
        logger.success("Verify Aviasales request '%s', dates from response validated successfully" % description)
    return success_dates


def verify_status_is_correct_in_db(policies_array, status_expected, description):
    success_status = True
    for policy_data in policies_array:
        # verify that status corresponds to the selected one
        if status_expected is not None and policy_data['status'] != status_expected:
            logger.fail("Verify status for policy_id = '%s': Failed (test EQ: actual '%s', expected '%s')" %
                        (str(policy_data['policy_id']), policy_data['status'], status_expected))
            success_status = False
    if success_status:
        logger.success("Verify Aviasales request '%s': statuses from response validated successfully" % description)
    return success_status


###############################################################################
# Functions implementing Test Cases
###############################################################################
@che_test_case("Aviasales request API format")
def aviasales_case_api_format():
    """Test case: verify API format of the aviasales request
    """
    date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relativedelta(years=1))
    values = {"http": (cfg_request_base_url + "d"), "interval": "3m", "timestamp": str(time_stamp)}
    parameters = [
        {"title": "incorrect request extention", "request": construct_aviasales_request(values), "code": 404},
        {"title": "all parameters are missing", "request": construct_aviasales_request(special="request_without_parameters"), "code": 403},
        {"title": "only authorization key is set as parameter", "request": construct_aviasales_request(special="request_with_key_only"), "code": 403}
    ]
    function_result = True
    for param in parameters:
        result, response = send_request_api_partner([(param["title"], param["request"], param["code"])],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request parameter 'request key' check")
def aviasales_case_request_key():
    """Test case: verify authorization key of the aviasales request
    """
    MONTHS_AMOUNT = 5
    key_list = [{"value": "a" + cfg_request_key, "description": "request_key is wrong"},
                {"value": "", "description": "request_key is empty"},
                {"value": "  ", "description": "request_key is made of spaces"},
                {"value": None, "description": "request_key is missing"},
                {"value": "0", "description": "request_key is zero"}
                ]
    # append keys list with all valid keys different from config value (correct value)
    for key in get_alternative_valid_keys():
        description = "valid request_key '%s' from other partner" % key
        key_list.append({"value": key, "description": description})

    request_interval = str(MONTHS_AMOUNT) + "m"  # predefined interval is set to MONTHS_AMOUNT months
    response_code = 403  # Forbidden
    function_result = True

    for key in key_list:
        date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relativedelta(months=MONTHS_AMOUNT))
        request_url = construct_aviasales_request(values={"interval": request_interval,
                                                          "timestamp": str(time_stamp),
                                                          "key": key["value"]})
        legend = "%s, limits=%s" % (key["description"], timeline)
        result, response = send_request_api_partner([(legend, request_url, response_code)],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request parameter 'partner_id' check")
def aviasales_case_partner_id():
    """Test case: verify partner ID parameter of the aviasales request
    """
    MONTHS_AMOUNT = 5
    partner_list = [{"value": get_not_existing_partner_id(), "description": "not existing partner_id"},
                    {"value": get_alternative_partner_id(), "description": "partner_id is from other valid partner"},
                    {"value": "", "description": "partner_id is empty"},
                    {"value": "  ", "description": "partner_id is made of spaces"},
                    {"value": None, "description": "partner_id is missing"},
                    {"value": "0", "description": "partner id is zero"}
                    ]
    request_interval = str(MONTHS_AMOUNT) + "m"  # predefined interval is set to MONTHS_AMOUNT months
    response_code = 403  # Forbidden
    function_result = True

    for partner in partner_list:
        date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relativedelta(months=MONTHS_AMOUNT))
        request_url = construct_aviasales_request(values={"interval": request_interval, "timestamp": str(time_stamp), "partner": partner["value"]})
        legend = "%s, limits=%s" % (partner["description"], timeline)
        result, response = send_request_api_partner([(legend, request_url, response_code)],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with no interval specified")
def aviasales_case_interval_missing():
    """Test case: request policies report with no interval specified and validate report data elements
    """
    MONTHS_AMOUNT = 1
    tc_name = "no interval specified"
    date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relativedelta(months=MONTHS_AMOUNT))
    request_url = construct_aviasales_request(values={"interval": None, "timestamp": str(time_stamp)})
    legend = tc_name + " " + timeline
    result, response = send_request_api_partner([(legend, request_url, 200)],
                                                schema_for_success="aviasales_response_with_success_schema",
                                                schema_for_error="aviasales_response_with_error_schema")
    result = result and validate_data_from_response(request_url, response, tc_name,
                                                    left_date=time_stamp, right_date=time_current)
    return result


@che_test_case("Aviasales request with predefined interval = '5h'")
def aviasales_case_interval_predefined_hours():
    """Test case: verify aviasales request parameter 'interval' for predefined value and validate report data elements
    """
    request_interval = "5h"
    tc_name = "predefined interval = '%s'" % request_interval
    function_result = True
    rel_delta = [relativedelta(months=6),
                 relativedelta(hours=5, seconds=1),
                 relativedelta(hours=5),
                 relativedelta(hours=2, minutes=30),
                 relativedelta()
                 ]
    for relative in rel_delta:
        date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relative)
        request_url = construct_aviasales_request(values={"interval": request_interval, "timestamp": str(time_stamp)})
        result, response = send_request_api_partner([(tc_name + timeline, request_url, 200)],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        result = result and validate_data_from_response(request_url, response, tc_name,
                                                        left_date=time_stamp, right_date=time_current)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with predefined interval = '5d'")
def aviasales_case_interval_predefined_days():
    """Test case: verify aviasales request parameter 'interval' for predefined value and validate report data elements
    """
    request_interval = "5d"
    tc_name = "predefined interval = '%s'" % request_interval
    function_result = True
    rel_delta = [relativedelta(months=6),
                 relativedelta(days=5, seconds=1),
                 relativedelta(days=5),
                 relativedelta(days=2, hours=12),
                 relativedelta()
                 ]
    for relative in rel_delta:
        date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relative)
        request_url = construct_aviasales_request(values={"interval": request_interval, "timestamp": str(time_stamp)})
        result, response = send_request_api_partner([(tc_name + timeline, request_url, 200)],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        result = result and validate_data_from_response(request_url, response, tc_name,
                                                        left_date=time_stamp, right_date=time_current)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with predefined interval = '5m'")
def aviasales_case_interval_predefined_months():
    """Test case: verify aviasales request parameter 'interval' for predefined value and validate report data elements
    """
    request_interval = "5m"
    tc_name = "predefined interval = '%s'" % request_interval
    function_result = True
    rel_delta = [relativedelta(months=12),
                 relativedelta(months=5, seconds=1),
                 relativedelta(months=5),
                 relativedelta(months=2, days=15),
                 relativedelta()
                 ]
    for relative in rel_delta:
        date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relative)
        request_url = construct_aviasales_request(values={"interval": request_interval, "timestamp": str(time_stamp)})
        result, response = send_request_api_partner([(tc_name + timeline, request_url, 200)],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        result = result and validate_data_from_response(request_url, response, tc_name,
                                                        left_date=time_stamp, right_date=time_current)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with predefined interval = '5y'")
def aviasales_case_interval_predefined_years():
    """Test case: verify aviasales request parameter 'interval' for predefined value and validate report data elements
    """
    request_interval = "5y"
    tc_name = "predefined interval = '%s'" % request_interval
    function_result = True
    rel_delta = [relativedelta(years=9),
                 relativedelta(years=5, seconds=1),
                 relativedelta(years=5),
                 relativedelta(years=2, months=6),
                 relativedelta()
                 ]
    for relative in rel_delta:
        date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relative)
        request_url = construct_aviasales_request(values={"interval": request_interval, "timestamp": str(time_stamp)})
        result, response = send_request_api_partner([(tc_name + timeline, request_url, 200)],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        result = result and validate_data_from_response(request_url, response, tc_name,
                                                        left_date=time_stamp, right_date=time_current)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with predefined interval with custom values")
def aviasales_case_interval_predefined_custom():
    """Test case: verify aviasales request parameter 'interval' for custom predefined values and validate report data elements
    """
    tc_name = "predefined interval with custom values"
    date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relativedelta(years=1))
    parameters = [
        {"interval": '3m', "title": "predefined interval is valid", "code": 200},
        {"interval": '3mpo', "title": "predefined interval has garbage in tail", "code": 200},
        {"interval": 'po3m', "title": "predefined interval has garbage in head", "code": 200},
        {"interval": '5k', "title": "predefined interval is wrong", "code": 400},
        {"interval": '5', "title": "predefined interval is wrong", "code": 400},
        {"interval": 'd', "title": "predefined interval is wrong", "code": 400},
        {"interval": '1234', "title": "predefined interval is wrong", "code": 400},
        {"interval": 'abcd', "title": "predefined interval is wrong", "code": 400},
        {"interval": '0', "title": "predefined interval is zero", "code": 400}
    ]
    function_result = True
    for param in parameters:
        request_url = construct_aviasales_request(values={"interval": param["interval"], "timestamp": str(time_stamp)})
        result, response = send_request_api_partner([("%s '%s', limits=%s" % (param["title"], param["interval"], timeline), request_url, param["code"])],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        if param["code"] == 200:
            result = result and validate_data_from_response(request_url, response, tc_name,
                                                            left_date=time_stamp, right_date=time_current)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with single date interval")
def aviasales_case_interval_single_date():
    """Test case: verify aviasales request parameter 'interval' with single date and validate report data elements
    """
    DAYS_AMOUNT = 90
    request_interval = (datetime.datetime.today() - relativedelta(days=DAYS_AMOUNT)).__format__("%d.%m.%Y")
    tc_name = "single date interval, date='%s'" % request_interval

    hour = datetime.datetime.now().hour
    minute = datetime.datetime.now().minute
    second = datetime.datetime.now().second
    rel_delta = [relativedelta(days=DAYS_AMOUNT*2),
                 relativedelta(days=DAYS_AMOUNT, hours=hour, minutes=minute, seconds=second),
                 relativedelta(days=DAYS_AMOUNT, seconds=1),
                 relativedelta(days=DAYS_AMOUNT),
                 relativedelta(days=DAYS_AMOUNT//2, hours=12),
                 relativedelta()
                 ]
    function_result = True
    # check the normal behaviour for interval with single date only
    for relative in rel_delta:
        date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relative)
        request_url = construct_aviasales_request(values={"interval": request_interval, "timestamp": str(time_stamp)})
        result, response = send_request_api_partner([(tc_name + " " + timeline, request_url, 200)],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        result = result and validate_data_from_response(request_url, response, tc_name,
                                                        left_date=time_stamp, right_date=time_current)
        function_result = result and function_result
    # check the behaviour if the timestamp is empty or absent
    timestamps = [{"value": "", "description": "timestamp is empty"},
                  {"value": "  ", "description": "timestamp is made of spaces"},
                  {"value": None, "description": "timestamp is missing"},
                  ]
    for time_stamp in timestamps:
        request_url = construct_aviasales_request(values={"interval": request_interval, "timestamp": str(time_stamp["value"])})
        result, response = send_request_api_partner([("%s, %s" % (tc_name, time_stamp["description"]), request_url, 200)],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        time_now = int(time.time())
        result = result and validate_data_from_response(request_url, response, tc_name,
                                                        left_date=time_now, right_date=time_now)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with single date interval with custom single date")
def aviasales_case_interval_single_date_custom():
    """Test case: verify aviasales request parameter 'interval' with custom single date values and validate report data elements
    """
    tc_name = "parameter 'interval' for single date check"
    DAYS_AMOUNT = 90
    string_garbage = "garbage"
    cyrillic_garbage = "фы!ва"
    # Note: When garbage contains '.' (dot) or digit and it is placed on the left of date - API tries to parse this
    # garbage, fails and returns error "400 The interval format is invalid". These limitation doesn't work if the
    # garbage is placed on the rigth of correct date, expected result is "200 OK"
    str_garbage_digit = "ga2rbage"  # expected response 400 when on the left of date
    cyr_garbage_dot = "фы!в.а"  # expected response 400 when on the left of date
    # Note: if digit is in the beginning of garbage then API tries to parse it either garbage is on the left or on the
    # right of the date, so expected response is "400 The interval format is invalid" in both cases.
    numeric_garbage = "5garbage"
    # Note: When the time is on the left of date - the date/time is parsed incorrectly, so expected response is 400.
    time_garbage = "12:00:00"  # expected response 400 when on the left of date

    target_date = datetime.datetime.today() - relativedelta(days=DAYS_AMOUNT)
    single_dates_list = [
        {"value": target_date.__format__("%d.%m.%Y"),
         "description": "single date is correct", "response_code": 200},

        {"value": target_date.__format__("%m.%Y"),
         "description": "single date has wrong format (no day)", "response_code": 400},

        {"value": target_date.__format__("%Y"),
         "description": "single date has wrong format (no day, no month)", "response_code": 400},

        {"value": target_date.__format__("0A.%m.%Y"),
         "description": "single date has wrong format (day is out of format)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1188
        # {"value": target_date.__format__("00.%m.%Y"),
        #  "description": "single date has wrong format (zero day)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1188
        # {"value": target_date.__format__("32.%m.%Y"),
        #  "description": "single date has wrong format (too large day)", "response_code": 400},

        {"value": target_date.__format__("%d.1A.%Y"),
         "description": "single date has wrong format (month is out of format)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1188
        # {"value": target_date.__format__("%d.00.%Y"),
        #  "description": "single date has wrong format (zero month)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1188
        # {"value": target_date.__format__("%d.13.%Y"),
        #  "description": "single date has wrong format (too large month)", "response_code": 400},

        {"value": target_date.__format__("%d.%m"),
         "description": "single date has wrong format (no year)", "response_code": 400},

        # Note: Year represented as two digits is valid year, so expected response is "OK" (200).
        #       Date is like 15.07.17, so the year is taken as "year 0017 AD", that assumed to be correct.
        {"value": target_date.__format__("%d.%m.%y"),
         "description": "single date is wrong for year (year of two digits)", "response_code": 200},

        # Note: Year represented as two digits with two alphas is valid year with garbage on the right side,
        #       garbage symbols are trimmed, so year is equal to 20, so expected response is "OK" (200).
        #       Date is like 15.07.20B5, so the year is taken as "year 0020 AD", that assumed to be correct.
        {"value": target_date.__format__("%d.%m.20B5"),
         "description": "single date has wrong format (year is out of format)", "response_code": 200},

        # Note: Year represented as zero is valid year, so expected response is "OK" (200).
        #       Date is like 15.07.00, so the year is taken as "year 0000 AD", that assumed to be correct.
        {"value": target_date.__format__("%d.%m.%y"),
         "description": "single date is wrong for year (zero year)", "response_code": 200},

        {"value": time_garbage + " " + target_date.__format__("%d.%m.%Y"),
         "description": "single date has wrong format (extra time on the left of date)", "response_code": 400},

        {"value": target_date.__format__("%d.%m.%Y") + " " + time_garbage,
         "description": "single date has wrong format (extra time on the right of date)", "response_code": 200},

        {"value": target_date.__format__("%d/%m/%Y"),
         "description": "single date has wrong format (slashes in date)", "response_code": 400},

        {"value": target_date.__format__("%Y.%m.%d"),
         "description": "single date has wrong format (date Y.m.d)", "response_code": 400},

        {"value": target_date.__format__("%Y.%d.%m"),
         "description": "single date has wrong format (date Y.d.m)", "response_code": 400},

        {"value": string_garbage + target_date.__format__("%d.%m.%Y"),
         "description": "single date has garbage symbols on the left of date", "response_code": 200},

        {"value": target_date.__format__("%d.%m.%Y") + string_garbage,
         "description": "single date has garbage symbols on the right of date", "response_code": 200},

        {"value": str_garbage_digit + target_date.__format__("%d.%m.%Y"),
         "description": "single date has garbage with digits on the left of date", "response_code": 400},

        {"value": target_date.__format__("%d.%m.%Y") + str_garbage_digit,
         "description": "single date has garbage with digits on the right of date", "response_code": 200},

        {"value": numeric_garbage + target_date.__format__("%d.%m.%Y"),
         "description": "single date has numeric garbage symbols on the left of date", "response_code": 400},

        {"value": target_date.__format__("%d.%m.%Y") + numeric_garbage,
         "description": "single date has numeric garbage symbols on the right of date", "response_code": 400},

        {"value": cyr_garbage_dot + target_date.__format__("%d.%m.%Y"),
         "description": "single date has garbage with cyrillic symbols on the left of date", "response_code": 400},

        {"value": target_date.__format__("%d.%m.%Y") + cyr_garbage_dot,
         "description": "single date has garbage with cyrillic symbols on the right of date", "response_code": 200},

        {"value": cyrillic_garbage + target_date.__format__("%d.%m.%Y"),
         "description": "single date has garbage with cyrillic symbols on the left of date", "response_code": 200},

        {"value": target_date.__format__("%d.%m.%Y") + cyrillic_garbage,
         "description": "single date has garbage with cyrillic symbols on the right of date", "response_code": 200}
    ]

    date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relativedelta(days=DAYS_AMOUNT + 1))
    function_result = True
    for request_interval in single_dates_list:
        request_url = construct_aviasales_request(values={"interval": request_interval["value"], "timestamp": str(time_stamp)})
        result, response = send_request_api_partner([(request_interval["description"], request_url, request_interval["response_code"])],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        if request_interval["response_code"] == 200:
            result = result and validate_data_from_response(request_url, response, tc_name,
                                                            left_date=time_stamp, right_date=time_current)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with single date interval with dates interval from past to past")
def aviasales_case_interval_custom_past_to_past():
    """Test case: verify aviasales request parameter 'interval' with dates interval from past to past and validate report data elements
    """
    MANY_DAYS_IN_THE_PAST = -3000
    SOME_DAYS_IN_THE_PAST = -30
    timestamp_left = create_random_timestamp_inside_interval(MANY_DAYS_IN_THE_PAST, SOME_DAYS_IN_THE_PAST - 1)
    timestamp_right = random.randint(timestamp_left, timestamp_plus_days(time.time(), SOME_DAYS_IN_THE_PAST))

    # get ("request_interval":string, "tc_name":string)
    request_interval, tc_name = format_intervals_for_testcase(timestamp_left, timestamp_right)
    # get [{"value":timestamp, "description":string}] for intervals
    timestamps = calc_parameters_for_custom_interval(timestamp_left, timestamp_right)

    function_result = True
    for time_stamp in timestamps:
        request_url = construct_aviasales_request(values={"interval": request_interval, "timestamp": str(time_stamp["value"])})
        result, response = send_request_api_partner([("custom interval, %s" % (time_stamp["description"]), request_url, 200)],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        result = result and validate_data_from_response(request_url, response, tc_name,
                                                        left_date=timestamp_left, right_date=timestamp_right)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with single date interval with dates interval from past to current moment")
def aviasales_case_interval_custom_past_to_present():
    """Test case: verify aviasales request parameter 'interval' with dates interval from past to current moment and validate report data elements
    """
    MANY_DAYS_IN_THE_PAST = -3000
    DAYS_FROM_NOW = 0
    timestamp_now = time.time()
    timestamp_left = create_random_timestamp_inside_interval(MANY_DAYS_IN_THE_PAST, DAYS_FROM_NOW, current_time=timestamp_now)
    timestamp_right = timestamp_plus_days(timestamp_now, DAYS_FROM_NOW)

    # get ("request_interval":string, "tc_name":string)
    request_interval, tc_name = format_intervals_for_testcase(timestamp_left, timestamp_right)
    # get [{"value":timestamp, "description":string}] for intervals
    timestamps = calc_parameters_for_custom_interval(timestamp_left, timestamp_right)

    function_result = True
    for time_stamp in timestamps:
        request_url = construct_aviasales_request(values={"interval": request_interval, "timestamp": str(time_stamp["value"])})
        result, response = send_request_api_partner([("custom interval, %s" % (time_stamp["description"]), request_url, 200)],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        result = result and validate_data_from_response(request_url, response, tc_name,
                                                        left_date=timestamp_left, right_date=timestamp_right)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with single date interval with dates interval from past to future")
def aviasales_case_interval_custom_past_to_future():
    """Test case: verify aviasales request parameter 'interval' with dates interval from past to future and validate report data elements
    """
    DAYS_IN_THE_PAST = -30
    SOME_DAYS_IN_THE_FUTURE = 5
    DAYS_FROM_NOW = 0
    timestamp_now = time.time()
    timestamp_left = create_random_timestamp_inside_interval(DAYS_IN_THE_PAST, DAYS_FROM_NOW, current_time=timestamp_now)
    timestamp_right = timestamp_plus_days(timestamp_now, SOME_DAYS_IN_THE_FUTURE)

    # get ("request_interval":string, "tc_name":string)
    request_interval, tc_name = format_intervals_for_testcase(timestamp_left, timestamp_right)
    # get [{"value":timestamp, "description":string}] for intervals
    timestamps = calc_parameters_for_custom_interval(timestamp_left, timestamp_right)

    function_result = True
    for time_stamp in timestamps:
        request_url = construct_aviasales_request(values={"interval": request_interval, "timestamp": str(time_stamp["value"])})
        result, response = send_request_api_partner([("custom interval, %s" % (time_stamp["description"]), request_url, 200)],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        result = result and validate_data_from_response(request_url, response, tc_name,
                                                        left_date=timestamp_left, right_date=timestamp_right)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with single date interval with dates interval from future to future")
def aviasales_case_interval_custom_present_to_future():
    """Test case: verify aviasales request parameter 'interval' with dates interval from future to future and validate report data elements
    """
    SOME_DAYS_IN_THE_FUTURE = 14
    DAYS_AMOUNT = 5
    DAYS_FROM_NOW = 0
    timestamp_left = create_random_timestamp_inside_interval(DAYS_FROM_NOW, SOME_DAYS_IN_THE_FUTURE)
    timestamp_right = timestamp_plus_days(timestamp_left, DAYS_AMOUNT)

    # get ("request_interval":string, "tc_name":string)
    request_interval, tc_name = format_intervals_for_testcase(timestamp_left, timestamp_right)
    # get [{"value":timestamp, "description":string}] for intervals
    timestamps = calc_parameters_for_custom_interval(timestamp_left, timestamp_right)

    function_result = True
    for time_stamp in timestamps:
        request_url = construct_aviasales_request(values={"interval": request_interval, "timestamp": str(time_stamp["value"])})
        result, response = send_request_api_partner([("custom interval, %s" % (time_stamp["description"]), request_url, 200)],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        result = result and validate_data_from_response(request_url, response, tc_name,
                                                        left_date=timestamp_left, right_date=timestamp_right)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with single date interval with dates interval custom values")
def aviasales_case_interval_custom_dates():
    """Test case: verify aviasales request parameter 'interval' with dates interval custom values and validate report data elements
    """
    tc_name = "parameter 'interval' for complex date check"
    MONTHS_AMOUNT = 3
    string_garbage = "qwerty"
    cyrillic_garbage = "фы!ва"
    date_now = datetime.datetime.now()
    date_calculated = datetime.datetime.now() - relativedelta(months=MONTHS_AMOUNT)
    intervals_list = [
        {"value": "", "description": "interval is empty", "response_code": 200},
        {"value": "  ", "description": "interval is made of spaces", "response_code": 200},
        {"value": None, "description": "interval is missing", "response_code": 200},

        # FIXME: commented due to expected failure CHEB-1189
        # {"interval_left": date_now.__format__("01.%m.%Y 23:59:59"),
        #  "interval_right": date_calculated.__format__("01.%m.%Y 00:00:00"),
        #  "description": "interval is wrong for dates ordering", "response_code": 400},

        {"interval_left": date_calculated.__format__("00:00:00 15.%m.%Y"),
         "interval_right": date_now.__format__("01.%m.%Y 23:59:59"),
         "description": "first interval is wrong for date and time ordering", "response_code": 400},

        {"interval_left": date_calculated.__format__("15.%m.%Y 00:00:00"),
         "interval_right": date_now.__format__("23:59:59 01.%m.%Y"),
         "description": "second interval is wrong for date and time ordering", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1189
        # {"value": date_calculated.__format__("15.%m.%Y 00:00:00") + " " + date_now.__format__("01.%m.%Y 23:59:59"),
        #  "description": "interval has wrong format (space as dates divider)", "response_code": 400},

        {"interval_left": string_garbage + date_calculated.__format__("15.%m.%Y 00:00:00"),
         "interval_right": date_now.__format__("01.%m.%Y 23:59:59"),
         "description": "interval has wrong format (garbage on the left of interval)", "response_code": 200},

        {"interval_left": date_calculated.__format__("15.%m.%Y 00:00:00"),
         "interval_right": date_now.__format__("01.%m.%Y 23:59:59") + string_garbage,
         "description": "interval has wrong format (garbage on the right of interval)", "response_code": 200},

        {"interval_left": cyrillic_garbage + date_calculated.__format__("15.%m.%Y 00:00:00"),
         "interval_right": date_now.__format__("01.%m.%Y 23:59:59"),
         "description": "interval has wrong format (cyrillic garbage on the left of interval)", "response_code": 200},

        {"interval_left": date_calculated.__format__("15.%m.%Y 00:00:00"),
         "interval_right": date_now.__format__("01.%m.%Y 23:59:59") + cyrillic_garbage,
         "description": "interval has wrong format (cyrillic garbage on the right of interval)", "response_code": 200}
    ]
    date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relativedelta(months=MONTHS_AMOUNT))
    function_result = True
    for request_interval in intervals_list:
        if "value" in request_interval.keys():
            interval = request_interval["value"]
        else:
            interval = ("%s-%s" % (request_interval["interval_left"], request_interval["interval_right"]))

        request_url = construct_aviasales_request(values={"interval": interval, "timestamp": str(time_stamp)})
        result, response = send_request_api_partner([("%s" % (request_interval["description"]), request_url, request_interval["response_code"])],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        if request_interval["response_code"] == 200:
            result = result and validate_data_from_response(request_url, response, tc_name,
                                                            left_date=time_stamp, right_date=time_current)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with single date interval with dates interval custom values")
def aviasales_case_interval_custom_dates_first_date():
    """Test case: verify aviasales request parameter 'interval' with dates interval custom values and validate report data elements
    """
    tc_name = "parameter 'interval' first date check"
    MONTHS_AMOUNT = 1
    date_calculated = (datetime.datetime.now() - relativedelta(months=MONTHS_AMOUNT))
    interval_right = (datetime.datetime.now()).__format__("01.%m.%Y 23:59:59")
    intervals_list = [
        {"interval_left": date_calculated.__format__("%m.%Y 00:00:00"),
         "interval_right": interval_right,
         "description": "first date is wrong (no day)", "response_code": 400},

        {"interval_left": date_calculated.__format__("%Y 00:00:00"),
         "interval_right": interval_right,
         "description": "first date is wrong (no day, no month)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1188
        # {"interval_left": date_calculated.__format__("00.%m.%Y 00:00:00"),
        #  "interval_right": interval_right,
        #  "description": "first date is wrong (zero day)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1188
        # {"interval_left": date_calculated.__format__("32.%m.%Y 00:00:00"),
        #  "interval_right": interval_right,
        #  "description": "first date is wrong (too large day)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1188
        # {"interval_left": date_calculated.__format__("15.00.%Y 00:00:00"),
        #  "interval_right": interval_right,
        #  "description": "first date is wrong (zero month)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1188
        # {"interval_left": date_calculated.__format__("15.13.%Y 00:00:00"),
        #  "interval_right": interval_right,
        #  "description": "first date is wrong (too large month)", "response_code": 400},

        {"interval_left": date_calculated.__format__("15.%m 00:00:00"),
         "interval_right": interval_right,
         "description": "first date is wrong (no year)", "response_code": 400},

        # Note: Year represented as two digits is valid year, so expected response is "OK" (200).
        #       Date is like 15.07.17, so the year is taken as "year 0017 AD", that assumed to be correct.
        {"interval_left": date_calculated.__format__("15.%m.%y 00:00:00"),
         "interval_right": interval_right,
         "description": "first date is wrong (year of two digits)", "response_code": 200},

        {"interval_left": date_calculated.__format__("15.%m.20BA 00:00:00"),
         "interval_right": interval_right,
         "description": "first date is wrong (year in wrong format)", "response_code": 400},

        {"interval_left": date_calculated.__format__("00:00:00"),
         "interval_right": interval_right,
         "description": "first date is wrong (missing date)", "response_code": 400},

        {"interval_left": date_calculated.__format__("15/%m/%Y 00:00:00"),
         "interval_right": interval_right,
         "description": "first date is wrong (slashes in first date)", "response_code": 400},

        {"interval_left": date_calculated.__format__("%Y.%m.15 00:00:00"),
         "interval_right": interval_right,
         "description": "first date is wrong (first date Y.m.d)", "response_code": 400},

        {"interval_left": date_calculated.__format__("%Y.15.%m 00:00:00"),
         "interval_right": interval_right,
         "description": "first date is wrong (first date Y.d.m)", "response_code": 400}
    ]

    date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relativedelta(months=MONTHS_AMOUNT+1))
    function_result = True
    for request_interval in intervals_list:
        interval = ("%s-%s" % (request_interval["interval_left"], request_interval["interval_right"]))
        request_url = construct_aviasales_request(values={"interval": interval, "timestamp": str(time_stamp)})
        result, response = send_request_api_partner([("%s" % (request_interval["description"]), request_url, request_interval["response_code"])],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema",)
        if request_interval["response_code"] == 200:
            result = result and validate_data_from_response(request_url, response, tc_name,
                                                            left_date=time_stamp, right_date=time_current)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with single date interval with dates interval custom values")
def aviasales_case_interval_custom_dates_first_time():
    """Test case: verify aviasales request parameter 'interval' with dates interval custom values and validate report data elements
    """
    tc_name = "parameter 'interval' first time check"
    MONTHS_AMOUNT = 1
    interval_left = (datetime.datetime.now() - relativedelta(months=MONTHS_AMOUNT)).__format__("15.%m.%Y ")
    interval_right = (datetime.datetime.now()).__format__("01.%m.%Y 23:59:59")
    intervals_list = [
        # FIXME: commented due to expected failure CHEB-1189
        # {"interval_left": interval_left + "23:60:60",
        #  "interval_right": interval_right,
        #  "description": "first time is wrong (day time overflow)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1189
        # {"interval_left": interval_left + "24:00:00",
        #  "interval_right": interval_right,
        #  "description": "first time is wrong (hours overflow)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1189
        # {"interval_left": interval_left + "00:60:00",
        #  "interval_right": interval_right,
        #  "description": "first time is wrong (minutes overflow)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1189
        # {"interval_left": interval_left + "00:00:60",
        #  "interval_right": interval_right,
        #  "description": "first time is wrong (seconds overflow)", "response_code": 400},

        {"interval_left": interval_left + "0A:00:00",
         "interval_right": interval_right,
         "description": "first time is wrong (incorrect hour)", "response_code": 400},

        {"interval_left": interval_left + "00:1B:00",
         "interval_right": interval_right,
         "description": "first time is wrong (incorrect minutes)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1189
        # {"interval_left": interval_left + "00:00:2K",
        #  "interval_right": interval_right,
        #  "description": "first time is wrong (incorrect seconds)", "response_code": 400},

        {"interval_left": interval_left + "02",
         "interval_right": interval_right,
         "description": "first time is wrong (incorrect time format)", "response_code": 400},

        {"interval_left": interval_left[:-1],
         "interval_right": interval_right,
         "description": "first time is wrong (missing time)", "response_code": 400}
    ]

    date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relativedelta(months=MONTHS_AMOUNT+1))
    function_result = True
    for request_interval in intervals_list:
        interval = ("%s-%s" % (request_interval["interval_left"], request_interval["interval_right"]))
        request_url = construct_aviasales_request(values={"interval": interval, "timestamp": str(time_stamp)})
        result, response = send_request_api_partner([("%s" % (request_interval["description"]), request_url, request_interval["response_code"])],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        if request_interval["response_code"] == 200:
            result = result and validate_data_from_response(request_url, response, tc_name,
                                                            left_date=time_stamp, right_date=time_current)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with single date interval with dates interval custom values")
def aviasales_case_interval_custom_dates_second_date():
    """Test case: verify aviasales request parameter 'interval' with dates interval custom values and validate report data elements
    """
    tc_name = "parameter 'interval' second date check"
    MONTHS_AMOUNT = 1
    interval_left = (datetime.datetime.now() - relativedelta(months=MONTHS_AMOUNT)).__format__("01.%m.%Y 23:59:59")
    date_now = (datetime.datetime.now())
    intervals_list = [
        {"interval_left": interval_left,
         "interval_right": date_now.__format__("%m.%Y 23:59:59"),
         "description": "second date is wrong (no day)", "response_code": 400},

        {"interval_left": interval_left,
         "interval_right": date_now.__format__("%Y 23:59:59"),
         "description": "second date is wrong (no day, no month)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1188
        # {"interval_left": interval_left,
        #  "interval_right": date_now.__format__("00.%m.%Y 23:59:59"),
        #  "description": "second date is wrong (zero day)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1188
        # {"interval_left": interval_left,
        #  "interval_right": date_now.__format__("32.%m.%Y 23:59:59"),
        #  "description": "second date is wrong (too large day)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1188
        # {"interval_left": interval_left,
        #  "interval_right": date_now.__format__("01.00.%Y 23:59:59"),
        #  "description": "second date is wrong (zero month)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1188
        # {"interval_left": interval_left,
        #  "interval_right": date_now.__format__("01.13.%Y 23:59:59"),
        #  "description": "second date is wrong (too large month)", "response_code": 400},

        {"interval_left": interval_left,
         "interval_right": date_now.__format__("01.%m 23:59:59"),
         "description": "second date is wrong (no year)", "response_code": 400},

        # Note: Year represented as two digits is valid year, so expected response is "OK" (200).
        #       Date is like 15.07.17, so the year is taken as "year 0017 AD", that assumed to be correct.
        {"interval_left": interval_left,
         "interval_right": date_now.__format__("01.%m.%y 23:59:59"),
         "description": "second date is wrong (year of two digits)", "response_code": 200},

        {"interval_left": interval_left,
         "interval_right": date_now.__format__("01.%m.20BA 23:59:59"),
         "description": "second date is wrong (year in wrong format)", "response_code": 400},

        {"interval_left": interval_left,
         "interval_right": date_now.__format__("23:59:59"),
         "description": "second date is wrong (missing date)", "response_code": 400},

        {"interval_left": interval_left,
         "interval_right": date_now.__format__("01/%m/%Y 23:59:59"),
         "description": "second date is wrong (slashes in second date)", "response_code": 400},

        {"interval_left": interval_left,
         "interval_right": date_now.__format__("%Y.%m.01 23:59:59"),
         "description": "second date is wrong (second date Y.m.d)", "response_code": 400},

        {"interval_left": interval_left,
         "interval_right": date_now.__format__("%Y.01.%m 23:59:59"),
         "description": "second date is wrong (second date Y.d.m)", "response_code": 400}
    ]

    date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relativedelta(months=MONTHS_AMOUNT+1))
    function_result = True
    for request_interval in intervals_list:
        interval = ("%s-%s" % (request_interval["interval_left"], request_interval["interval_right"]))
        request_url = construct_aviasales_request(values={"interval": interval, "timestamp": str(time_stamp)})
        result, response = send_request_api_partner([("%s" % (request_interval["description"]), request_url, request_interval["response_code"])],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        if request_interval["response_code"] == 200:
            result = result and validate_data_from_response(request_url, response, tc_name,
                                                            left_date=time_stamp, right_date=time_current)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request with single date interval with dates interval custom values")
def aviasales_case_interval_custom_dates_second_time():
    """Test case: verify aviasales request parameter 'interval' with dates interval custom values and validate report data elements
    """
    tc_name = "parameter 'interval' second time check"
    MONTHS_AMOUNT = 1
    interval_left = (datetime.datetime.now() - relativedelta(months=MONTHS_AMOUNT)).__format__("15.%m.%Y 00:00:00")
    interval_right = (datetime.datetime.now()).__format__("01.%m.%Y ")
    intervals_list = [
        # FIXME: commented due to expected failure CHEB-1189
        # {"interval_left": interval_left,
        #  "interval_right": interval_right + "23:60:60",
        #  "description": "second time is wrong (day time overflow)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1189
        # {"interval_left": interval_left,
        #  "interval_right": interval_right + "24:00:00",
        #  "description": "second time is wrong (hours overflow)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1189
        # {"interval_left": interval_left,
        #  "interval_right": interval_right + "22:60:00",
        #  "description": "second time is wrong (minutes overflow)", "response_code": 400},

        # FIXME: commented due to expected failure CHEB-1189
        # {"interval_left": interval_left,
        #  "interval_right": interval_right + "22:00:60",
        #  "description": "second time is wrong (seconds overflow)", "response_code": 400},

        {"interval_left": interval_left,
         "interval_right": interval_right + "0A:59:59",
         "description": "second time is wrong (incorrect hour)", "response_code": 400},

        {"interval_left": interval_left,
         "interval_right": interval_right + "22:1B:00",
         "description": "second time is wrong (incorrect minutes)", "response_code": 400},

        {"interval_left": interval_left,
         "interval_right": interval_right + "22:00:2K",
         "description": "second time is wrong (incorrect seconds)", "response_code": 400},

        {"interval_left": interval_left,
         "interval_right": interval_right + "15",
         "description": "second time is wrong (incorrect time format)", "response_code": 400},

        {"interval_left": interval_left,
         "interval_right": interval_right[:-1],
         "description": "second time is wrong (missing time)", "response_code": 400}
    ]

    date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relativedelta(months=MONTHS_AMOUNT+1))
    function_result = True
    for request_interval in intervals_list:
        interval = ("%s-%s" % (request_interval["interval_left"], request_interval["interval_right"]))
        request_url = construct_aviasales_request(values={"interval": interval, "timestamp": str(time_stamp)})
        result, response = send_request_api_partner([("%s" % (request_interval["description"]), request_url, request_interval["response_code"])],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        if request_interval["response_code"] == 200:
            result = result and validate_data_from_response(request_url, response, tc_name,
                                                            left_date=time_stamp, right_date=time_current)
        function_result = result and function_result
    return function_result


@che_test_case("Aviasales request parameter 'timestamp' check")
def aviasales_case_timestamp():
    """Test case: verify timestamp parameter values of the aviasales request
    """
    MONTHS_AMOUNT = 5
    valid_stamp = str(int(time.mktime((datetime.datetime.now() - relativedelta(months=MONTHS_AMOUNT+1)).timetuple())))
    intervals_list = ["h", "d", "m", "y"]
    stamps_list = [{"value": "", "description": "timestamp is empty", "response_code": 200},
                   {"value": "  ", "description": "timestamp is made of spaces", "response_code": 200},
                   {"value": None, "description": "timestamp is missing", "response_code": 200},
                   {"value": "abcdef", "description": "timestamp has wrong format", "response_code": 400},
                   {"value": str(valid_stamp) + ",5", "description": "timestamp is fractional with comma as delimiter", "response_code": 400},
                   {"value": str(valid_stamp) + ".5", "description": "timestamp is fractional with dot as delimiter", "response_code": 400}
                   ]

    function_result = True
    for interval in intervals_list:
        for timestamp in stamps_list:
            request_interval = str(MONTHS_AMOUNT) + interval
            request_url = construct_aviasales_request(values={"interval": request_interval, "timestamp": timestamp["value"]})
            result = send_request_api_partner([("timestamp check (%s), interval='%s'" % (timestamp["description"], request_interval), request_url, timestamp["response_code"])],
                                              schema_for_success="aviasales_response_with_success_schema",
                                              schema_for_error="aviasales_response_with_error_schema")
            function_result = result[0] and function_result
    return function_result


@che_test_case("Aviasales request optional parameter 'status' check")
def aviasales_case_status():
    """Test case: request policies report for custom status values and validate report data elements
    """
    MONTHS_AMOUNT = 1
    tc_name = "optional parameter 'status' check"

    status_list = [
        # FIXME: commented due to expected failure CHEB-1138
        # {"value": u'', "description": "status is empty", },
        # FIXME: commented due to expected failure CHEB-1138
        # {"value": u'  ', "description": "status is made of spaces"},
        {"value": None, "description": "status is missing"},
        # FIXME: commented due to expected failure CHEB-1138
        # {"value": u'paid', "description": "status has valid value 'paid'"},
        # FIXME: commented due to expected failure CHEB-1138
        # {"value": u'processing', "description": "status has valid value 'processing'"},
        {"value": u'canceled', "description": "status has valid value 'canceled'"},
        # FIXME: commented due to expected failure CHEB-1138
        # {"value": u'wrong', "description": "status has wrong value"},
        # FIXME: commented due to expected failure CHEB-1138
        # {"value": u'0', "description": "status is zero"}
    ]
    request_interval = str(MONTHS_AMOUNT) + "m"  # predefined interval is set to MONTHS_AMOUNT months
    response_code = 200  # Success
    function_result = True

    for status in status_list:
        date_now, date_past, time_current, time_stamp, timeline = calc_parameters_for_request(relativedelta(months=MONTHS_AMOUNT))
        request_url = construct_aviasales_request(values={"interval": request_interval, "timestamp": str(time_stamp), "status": status["value"]})
        result, response = send_request_api_partner([("%s, limits=%s" % (status["description"], timeline), request_url, response_code)],
                                                    schema_for_success="aviasales_response_with_success_schema",
                                                    schema_for_error="aviasales_response_with_error_schema")
        result = result and validate_data_from_response(request_url, response, tc_name,
                                                        left_date=time_stamp, right_date=time_current,
                                                        status_expected=status["value"])
        function_result = result and function_result
    return function_result


###############################################################################
# main test function
###############################################################################
@che_autotest(__file__)
def test_aviasales_report_check():
    """Test suite to verify the aviasales reports API request, its parameters and returned responses.
    """
    # validate the template schemas used in test
    result = validate_json_schema("aviasales_response_with_success_schema") \
             and validate_json_schema("aviasales_response_with_error_schema")
    with CheDb():
        logger.success("Database validation")
    logger.print_empty_line()

    test_cases = [
        aviasales_case_api_format,
        aviasales_case_request_key,
        aviasales_case_partner_id,
        aviasales_case_interval_missing,
        aviasales_case_interval_predefined_hours,
        aviasales_case_interval_predefined_days,
        aviasales_case_interval_predefined_months,
        aviasales_case_interval_predefined_years,
        aviasales_case_interval_predefined_custom,
        aviasales_case_interval_single_date,
        aviasales_case_interval_single_date_custom,
        aviasales_case_interval_custom_past_to_past,
        aviasales_case_interval_custom_past_to_present,
        aviasales_case_interval_custom_past_to_future,
        aviasales_case_interval_custom_present_to_future,
        aviasales_case_interval_custom_dates,
        aviasales_case_interval_custom_dates_first_date,
        aviasales_case_interval_custom_dates_first_time,
        aviasales_case_interval_custom_dates_second_date,
        aviasales_case_interval_custom_dates_second_time,
        aviasales_case_timestamp,
        aviasales_case_status
    ]
    return run_test_and_get_result(test_cases) and result


if __name__ == '__main__':
    test_aviasales_report_check()
