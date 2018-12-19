#!/usr/bin/env python3
# -*- coding: utf-8; -*-
import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse
import random

import common.logger as logger
import common.request as common_request
import common.randomize as randomize
from common.logger import PASS, FAIL
from common.system import che_autotest, che_test_case, run_test_and_get_result
from common.config_module import load, get_value_from_config
from common.database import CheDb
from common.tickets_api import construct_tickets_api_request
from common.randomize import get_random_string


###############################################################################
# Config values
###############################################################################
cfg_request_base_url = "http:" + get_value_from_config("[u'api'][u'url']").replace("/v2", "/v1") + "/imputed.json"

config = load("config/tickets.json")
cfg_request_key = config[u'request_key']
cfg_buyer_email = config[u'buyer_email']
cfg_buyer_lastname = config[u'buyer_lastname']
cfg_buyer_firstname = config[u'buyer_firstname']
cfg_tourist_birthday = config[u'tourist_birthday']
cfg_tourist_lastname = config[u'tourist_lastname']
cfg_tourist_firstname = config[u'tourist_firstname']
cfg_refid = config[u'refid']

tc_prefix = "Tickets Calculation request "


###############################################################################
# functions used in Test Cases
###############################################################################
def generate_random_key_ascii():
    """Generate random string made of ASCII characters to be used as an access key.
    Length of the returned string is the same as length of correct key.

    :return: random generated string with length of correct key
    """
    return get_random_string(size=len(urllib.parse.unquote(cfg_request_key)))  # make random key of ASCII characters


def generate_random_key_space_chars():
    """Generate random string made of spacechar characters. Length of the returned string is default for generation function.

    :return: random generated string
    """
    return urllib.parse.quote(randomize.get_random_spacechar_filled_string())  # make random key of ASCII characters


def generate_garbage_string(length=None):
    """Generate random string made of english alphabet alpha characters.

    :param int length: length of string to be generated
    :return: random generated string
    """
    if not length:
        length = random.choice([1, 2, 3, 5, 7, 10, 15, 16, 127])
    return get_random_string(size=length)


def generate_single_char_random_string():
    """Generate random string made of single english alphabet alpha character. Length of the returned string is 1.

    :return: random generated string
    """
    return get_random_string(size=1)


def generate_garbage_of_symbolic_string(length=None):
    """Generate random string made of symbolic characters.

    :param int length: length of string to be generated
    :return: random generated string
    """
    if not length:
        length = random.choice([1, 2, 3, 5, 7, 10, 15, 16, 127])
    return get_random_string(size=length, chars="~`!@#$%^&*()_+-=")


def generate_garbage_punctuation_string(length=None):
    """Generate random string made of punctuation characters.

    :param int length: length of string to be generated
    :return: random generated string
    """
    if not length:
        length = random.choice([1, 2, 3, 5, 7, 10, 15, 16, 127])
    return get_random_string(size=length, chars="(){}[].,:;!?")


def generate_random_string_as_number(negative=False, length=None):
    """Generate random string made of digit characters.

    :param boolean negative: if True then negative sign is set to represent negative value
    :param int length: length of string to be generated
    :return: random generated string
    """
    if not length:
        length = random.choice([1, 2, 3, 5, 7, 10, 15, 16, 127])
    set_digits = "0123456789"
    if negative:
        return "-" + get_random_string(size=length, chars=set_digits)
    return get_random_string(size=length, chars=set_digits)


def generate_random_string_as_number_fractional(comma_separation=False):
    """Generate random string representing fractional number with dot or comma as divider.
    Length of integer and fractional parts are random.

    :param boolean comma_separation: optional, if True then comma is used as separator, otherwise dot is used
    :return: random generated string
    """
    size_integer = random.choice([1, 2, 3, 5, 7, 10, 15, 16, 127])
    size_fractional = random.choice([1, 2, 3, 5, 7, 10, 15, 16, 127])
    set_digits = "0123456789"
    if comma_separation:
        return get_random_string(size=size_integer, chars=set_digits) + "," + get_random_string(size=size_fractional, chars=set_digits)
    return get_random_string(size=size_integer, chars=set_digits) + "." + get_random_string(size=size_fractional, chars=set_digits)


def make_single_char_random_replacement(source):
    """Replace single character in the string.
    """
    new_string = source
    while new_string == source:
        new_string = source
        index = random.randint(0, len(source) - 1)
        ch = generate_single_char_random_string()
        new_string = new_string.replace(source[index], ch)
    return new_string


def execute_tickets_calculation_requests(req_list):
    function_result = True
    for (description, value, response, expected) in req_list:
        logger.expected_result = expected
        result, response = common_request.send_request_api_partner([(description, value, response)],
                                                                   schema_for_success="tickets_api_calculation_success_schema",
                                                                   schema_for_error="api_error_without_description")
        logger.expected_result = PASS
        function_result = function_result and result
    return function_result


###############################################################################
# Functions implementing Test Cases
###############################################################################
@che_test_case(tc_prefix + "API format")
def tickets_api_calc_api_format():
    """TestCase: Request via API endpoint the tickets policy calculation and validate the whole request structure
    """
    req_list = [("default request", construct_tickets_api_request(), 200, PASS)]
    # Note: request extension is '.json'
    base_url_length = len(cfg_request_base_url)
    reqs_data = [
        ("extra-long request extension", cfg_request_base_url + generate_single_char_random_string(), 404, FAIL),
        ("wrong request extension, single char changed",
         cfg_request_base_url[:base_url_length-4] + make_single_char_random_replacement(cfg_request_base_url[base_url_length - 4:]),
         404, FAIL),
        ("incomplete request extension (3 chars left)", cfg_request_base_url[:base_url_length-1], 404, FAIL),
        ("incomplete request extension (2 chars left)", cfg_request_base_url[:base_url_length-2], 404, PASS),
        ("incomplete request extension (1 char left)", cfg_request_base_url[:base_url_length-3], 404, FAIL),
        ("missing request extension, but dot", cfg_request_base_url[:base_url_length-4], 404, PASS),
        ("missing request extension", cfg_request_base_url[:base_url_length-5], 404, PASS)
    ]
    req_list += [(description, construct_tickets_api_request(http=value), response, expected)
                 for description, value, response, expected in reqs_data]

    req_list.append(("all parameters are missing", construct_tickets_api_request(special="url_without_parameters"), 500, PASS))
    req_list.append(("only key is present as parameter", construct_tickets_api_request(special="url_with_key_only"), 500, PASS))
    req_list.append(("all insurance options are off",
                     construct_tickets_api_request(imputed_avia_accident="false", imputed_avia_cargo="false",
                                               imputed_cancel_travel="false", imputed_delay_dock="false",
                                               imputed_delay_regular="false"),
                     200, PASS))
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter 'key'")
def tickets_api_calc_key():
    """TestCase: Requests via API endpoint the tickets policy calculation and
    validate the key values and responses from API for different values.
    """
    param_name = "request key"
    reqs_data = [
        ("is wrong", generate_random_key_ascii(), 500, FAIL),
        ("is empty", "", 500, FAIL),
        ("is made of spacechars", generate_random_key_space_chars(), 500, FAIL),
        ("is missing", None, 500, FAIL),
        ("is zero", "0", 500, FAIL)
    ]
    req_list = [("%s %s" % (param_name, description), construct_tickets_api_request(key=value), response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[date_start]'")
def tickets_api_calc_datestart():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of start date and responses from API for different values
    """
    param_name = "date_start"
    # date used in calculations is 10 days in future
    temp_10days_date = (datetime.date.today() + datetime.timedelta(days=10))
    reqs_data = [
        ('is empty', '', 200, FAIL),
        ('is made of spacechars', generate_random_key_space_chars(), 500, PASS),
        ('is missing', None, 500, PASS),
        ('is zero', '0', 500, PASS),

        ('has garbage on the left', generate_garbage_string() + temp_10days_date.strftime('%d.%m.%Y'), 500, FAIL),
        ('has garbage on the right', temp_10days_date.strftime('%d.%m.%Y') + generate_garbage_string(), 500, FAIL),
        ('has extra time on the left', '05:37:21 ' + temp_10days_date.strftime('%d.%m.%Y'), 500, FAIL),
        ('has extra time on the right', temp_10days_date.strftime('%d.%m.%Y') + ' 05:37:21', 500, FAIL),

        ('has wrong year position', temp_10days_date.strftime('%Y.%d.%m'), 500, PASS),
        ('has wrong format (no day/month)', temp_10days_date.strftime('%m.%Y'), 500, PASS),
        ('has wrong format (no day, no month)', temp_10days_date.strftime('%Y'), 500, FAIL),
        ('has wrong format (no year)', temp_10days_date.strftime('%d.%m'), 500, FAIL),
        ('has wrong format (year of two digits)', temp_10days_date.strftime('%d.%m.%y'), 500, FAIL),
        ('has wrong format (slashes in date)', temp_10days_date.strftime('%d/%m/%Y'), 500, FAIL),

        ('has wrong format (too large day)', temp_10days_date.strftime('32.%m.%Y'), 500, PASS),
        ('has wrong format (day is out of format)', temp_10days_date.strftime('1A.%m.%Y'), 500, PASS),
        ('has wrong format (zero day)', temp_10days_date.strftime('00.%m.%Y'), 500, FAIL),

        ('has wrong format (too large month)', temp_10days_date.strftime('%d.13.%Y'), 500, PASS),
        ('has wrong format (month is out of format)', temp_10days_date.strftime('%d.0A.%Y'), 500, FAIL),
        ('has wrong format (zero month)', temp_10days_date.strftime('%d.00.%Y'), 500, FAIL),

        ('has wrong format (too large year)', temp_10days_date.strftime('%d.%m.5000'), 200, PASS),
        ('has wrong format (year is out of format)', temp_10days_date.strftime('%d.%m.20B5'), 500, PASS),
        ('has wrong format (zero year)', temp_10days_date.strftime('%d.%m.0000'), 500, FAIL)
    ]
    req_list = [("%s %s" % (param_name, description), construct_tickets_api_request(date_start=value), response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[date_end]'")
def tickets_api_calc_dateend():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of end date and responses from API for different values
    """
    param_name = "date_end"
    # date used in calculations is 10 days in future
    temp_10days_date = (datetime.date.today() + datetime.timedelta(days=10))
    reqs_data = [
        ('is empty', '', 200, PASS),
        ('is made of spacechars', generate_random_key_space_chars(), 500, PASS),
        ('is missing', None, 500, PASS),
        ('is zero', '0', 500, FAIL),

        ('garbage on the left', generate_garbage_string() + temp_10days_date.strftime('%d.%m.%Y'), 500, FAIL),
        ('garbage on the right', temp_10days_date.strftime('%d.%m.%Y') + generate_garbage_string(), 500, FAIL),
        ('extra time on the left', '05:37:21 ' + temp_10days_date.strftime('%d.%m.%Y'), 500, FAIL),
        ('extra time on the right', temp_10days_date.strftime('%d.%m.%Y') + ' 05:37:21', 500, FAIL),

        ('has wrong year position', temp_10days_date.strftime('%Y.%d.%m'), 500, PASS),
        ('has wrong format (no day/month)', temp_10days_date.strftime('%m.%Y'), 500, PASS),
        ('has wrong format (no day, no month)', temp_10days_date.strftime('%Y'), 500, FAIL),
        ('has wrong format (no year)', temp_10days_date.strftime('%d.%m'), 500, FAIL),
        ('has wrong format (year of two digits)', temp_10days_date.strftime('%d.%m.%y'), 500, FAIL),
        ('has wrong format (slashes in date)', temp_10days_date.strftime('%d/%m/%Y'), 500, FAIL),

        ('has wrong format (too large day)', temp_10days_date.strftime('32.%m.%Y'), 500, PASS),
        ('has wrong format (day is out of format)', temp_10days_date.strftime('1A.%m.%Y'), 500, PASS),
        ('has wrong format (zero day)', temp_10days_date.strftime('00.%m.%Y'), 500, FAIL),

        ('has wrong format (too large month)', temp_10days_date.strftime('%d.13.%Y'), 500, PASS),
        ('has wrong format (month is out of format)', temp_10days_date.strftime('%d.0A.%Y'), 500, FAIL),
        ('has wrong format (zero month)', temp_10days_date.strftime('%d.00.%Y'), 500, FAIL),

        ('has wrong format (too large year)', temp_10days_date.strftime('%d.%m.5000'), 500, FAIL),
        ('has wrong format (year is out of format)', temp_10days_date.strftime('%d.%m.20B5'), 500, PASS),
        ('has wrong format (zero year)', temp_10days_date.strftime('%d.%m.0000'), 50, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description), construct_tickets_api_request(date_end=value), response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter 'Company'")
def tickets_api_calc_company():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of company parameter and responses from API for different values
    """
    param_name = "Company"
    reqs_data = [
        ("is empty", "", 500, FAIL),
        ("is made of spacechars", generate_random_key_space_chars(), 500, FAIL),
        ("is missing", None, 500, FAIL),
        ("is zero", '0', 500, FAIL),
        ("doesn't exist", 'wrong_company', 500, FAIL)
    ]
    dict_of_companies = CheDb().get_insurance_companies_list(disabled=0)
    for company in dict_of_companies:
        reqs_data.append(("Company is '%s'" % dict_of_companies[company].encode('utf-8'), company, 200, PASS))

    req_list = [("%s %s" % (param_name, description), construct_tickets_api_request(company=value), response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter 'Tourists'")
def tickets_api_calc_tourists():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of tourists parameter and responses from API for different values
    """
    param_name = "Number of tourists"
    reqs_data = [
        ("is missing", None, 500, FAIL),
        ("is made of spacechars", generate_random_key_space_chars(), 500, FAIL),
        ("is zero", '0', 500, FAIL),
        ("is negative", '-1', 500, FAIL),
        ("is not in valid format", 'A1', 500, FAIL),
        ("is string", 'AB', 500, FAIL),
        ("(3) is more than named by default (1)", '3', 500, FAIL)
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(tourists=value), response, expected)
                for description, value, response, expected in reqs_data]

    additional_tourist = [{"firstname": "Test", "lastname": "Test", "birthday": cfg_tourist_birthday}]
    reqs_data = [
        ("(1) is less than the number of tourists in list (2)", '1', additional_tourist, 500, FAIL),
        ("(2) is equal to the number of tourists in list (2)", '2', additional_tourist, 200, PASS),
        ("(3) is more than the number of tourists in list (2)", '3', additional_tourist, 500, FAIL)
    ]
    req_list += [("%s %s" % (param_name, description),
                  construct_tickets_api_request(tourists=value, tourist_list=add_tourist), response, expected)
                 for description, value, add_tourist, response, expected in reqs_data]

    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[imputed.Avia_Cargo]'")
def tickets_api_calc_imputed_avia_cargo():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Imputed.Avia_Cargo] and responses from API for different values
    """
    param_name = "[imputed.avia_cargo]"
    reqs_data = [
        ("is empty", "", 200, PASS),
        ("is made of spacechars", generate_random_key_space_chars(), 200, PASS),
        ("is missing", None, 200, PASS),
        ("is zero", "0", 200, PASS),
        ("= False", "false", 200, PASS),
        ("= True", "true", 200, PASS),
        ("is garbage", generate_garbage_string(), 500, FAIL),
        ("is symbolic garbage", generate_garbage_of_symbolic_string(), 500, FAIL),
        ("is number", generate_random_string_as_number(), 500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description), construct_tickets_api_request(imputed_avia_cargo=value), response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[imputed.Delay_Regular]'")
def tickets_api_calc_imputed_delay_regular():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Imputed.Delay_Regular] and responses from API for different values
    """
    param_name = "[imputed.delay_regular]"
    reqs_data = [
        ("is empty", "", 200, PASS),
        ("is made of spacechars", generate_random_key_space_chars(), 200, PASS),
        ("is missing", None, 200, PASS),
        ("is zero", "0", 200, PASS),
        ("= False", "false", 200, PASS),
        ("= True", "true", 200, PASS),
        ("is garbage", generate_garbage_string(), 500, FAIL),
        ("is symbolic garbage", generate_garbage_of_symbolic_string(), 500, FAIL),
        ("is number", generate_random_string_as_number(), 500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(imputed_delay_regular=value), response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[imputed.Cancel_Travel]'")
def tickets_api_calc_imputed_cancel_travel():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Imputed.Cancel_Travel] and responses from API for different values
    """
    param_name = "[imputed.cancel_travel]"
    reqs_data = [
        ("is empty", "", 200, PASS),
        ("is made of spacechars", generate_random_key_space_chars(), 200, PASS),
        ("is missing", None, 200, PASS),
        ("is zero", "0", 200, PASS),
        ("= False", "false", 200, PASS),
        ("= True", "true", 200, PASS),
        ("is garbage", generate_garbage_string(), 500, FAIL),
        ("is symbolic garbage", generate_garbage_of_symbolic_string(), 500, FAIL),
        ("is number", generate_random_string_as_number(), 500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(imputed_cancel_travel=value), response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[imputed.Avia_Accident]'")
def tickets_api_calc_imputed_avia_accident():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Imputed.Avia_Accident] and responses from API for different values
    """
    param_name = "[imputed.avia_accident]"
    reqs_data = [
        ("is empty", "", 200, PASS),
        ("is made of spacechars", generate_random_key_space_chars(), 200, PASS),
        ("is missing", None, 200, PASS),
        ("is zero", "0", 200, PASS),
        ("= False", "false", 200, PASS),
        ("= True", "true", 200, PASS),
        ("is garbage", generate_garbage_string(), 500, FAIL),
        ("is symbolic garbage", generate_garbage_of_symbolic_string(), 500, FAIL),
        ("is number", generate_random_string_as_number(), 500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(imputed_avia_accident=value),
                 response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[imputed.Delay_Dock]'")
def tickets_api_calc_imputed_delay_dock():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Imputed.Delay_Dock] and responses from API for different values
    """
    param_name = "[imputed.delay_dock]"
    # Note: imputed_avia_cargo is required to be set to make policy with active option
    reqs_data = [
        ("is empty", "", 200, PASS),
        ("is made of spacechars", generate_random_key_space_chars(), 200, PASS),
        ("is missing", None, 200, PASS),
        ("is zero", "0", 200, PASS),
        ("= False", "false", 200, PASS),
        ("= True", "true", 200, PASS),
        ("is garbage", generate_garbage_string(), 500, FAIL),
        ("is symbolic garbage", generate_garbage_of_symbolic_string(), 500, FAIL),
        ("is number", generate_random_string_as_number(), 500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(imputed_delay_dock=value, imputed_avia_cargo="true"),
                 response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[Params][Price][imputed.Avia_Cargo]'")
def tickets_api_calc_params_price_imputed_avia_cargo():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Params][Price][Imputed.Avia_Cargo] and responses from API for different values
    """
    param_name = "[params][price][imputed.avia_cargo]"
    reqs_data = [
        ("is empty", "", 500, FAIL),
        ("is made of spacechars", generate_random_key_space_chars(), 500, FAIL),
        ("is missing", None, 500, FAIL),
        ("is zero", "0", 500, FAIL),
        ("= False", "false", 500, FAIL),
        ("= True", "true", 500, FAIL),
        ("is garbage", generate_garbage_string(), 500, FAIL),
        ("is symbolic garbage", generate_garbage_of_symbolic_string(), 500, FAIL),
        ("is fractional number with dot", generate_random_string_as_number_fractional(), 200, PASS),
        ("is fractional number with comma", generate_random_string_as_number_fractional(comma_separation=True), 500, FAIL),
        ("has wrong format", "AB45", 500, FAIL),
        ("is negative", generate_random_string_as_number(negative=True), 500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(params_price_imputed_avia_cargo=value, imputed_avia_cargo="true"),
                 response, expected)
                for description, value, response, expected in reqs_data]
    req_list.append(("%s is correct, but [imputed.avia_cargo] = False" % param_name,
                     construct_tickets_api_request(params_price_imputed_avia_cargo="2000", imputed_avia_cargo="false"),
                     200, PASS))
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[Params][Price][imputed.Delay_Regular]'")
def tickets_api_calc_params_price_imputed_delay_regular():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Params][Price][Imputed.Delay_Regular] and responses from API for different values
    """
    param_name = "[params][price][imputed.delay_regular]"
    reqs_data = [
        ("is empty", "", 500, FAIL),
        ("is made of spacechars", generate_random_key_space_chars(), 500, FAIL),
        ("is missing", None, 500, FAIL),
        ("is zero", "0", 500, FAIL),
        ("= False", "false", 500, FAIL),
        ("= True", "true", 500, FAIL),
        ("is garbage", generate_garbage_string(), 500, FAIL),
        ("is symbolic garbage", generate_garbage_of_symbolic_string(), 500, FAIL),
        ("is fractional number with dot", generate_random_string_as_number_fractional(), 200, PASS),
        ("is fractional number with comma", generate_random_string_as_number_fractional(comma_separation=True), 500, FAIL),
        ("has wrong format", "AB45", 500, FAIL),
        ("is negative", generate_random_string_as_number(negative=True), 500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(params_price_imputed_delay_regular=value, imputed_delay_regular="true"),
                 response, expected)
                for description, value, response, expected in reqs_data]
    req_list.append(("%s is correct, but [imputed.delay_regular] = False" % param_name,
                     construct_tickets_api_request(params_price_imputed_delay_regular="2000",
                                               imputed_delay_regular="false",
                                               imputed_delay_dock="false"),
                     200, PASS))
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[Params][Price][imputed.Cancel_Travel]'")
def tickets_api_calc_params_price_imputed_cancel_travel():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Params][Price][Imputed.Cancel_Travel] and responses from API for different values
    """
    param_name = "[params][price][imputed.cancel_travel]"
    reqs_data = [
        ("is empty", "", 500, FAIL),
        ("is made of spacechars", generate_random_key_space_chars(), 500, FAIL),
        ("is missing", None, 500, FAIL),
        ("is zero", "0", 500, FAIL),
        ("= False", "false", 500, FAIL),
        ("= True", "true", 500, FAIL),
        ("is garbage", generate_garbage_string(), 500, FAIL),
        ("is symbolic garbage", generate_garbage_of_symbolic_string(), 500, FAIL),
        ("is fractional number with dot", generate_random_string_as_number_fractional(),  200, FAIL),
        ("is fractional number with comma", generate_random_string_as_number_fractional(comma_separation=True), 500, FAIL),
        ("has wrong format", "AB45", 500, FAIL),
        ("is negative", generate_random_string_as_number(negative=True), 500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(params_price_imputed_cancel_travel=value, imputed_cancel_travel="true"),
                 response, expected)
                for description, value, response, expected in reqs_data]
    req_list.append(("%s is correct, but [imputed.cancel_travel] = False" % param_name,
                     construct_tickets_api_request(params_price_imputed_cancel_travel="2000",
                                                   imputed_cancel_travel="false"),
                     200, PASS))
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[Params][Price][imputed.Avia_Accident]'")
def tickets_api_calc_params_price_imputed_avia_accident():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Params][Price][Imputed.Avia_Accident] and responses from API for different values
    """
    param_name = "[params][price][imputed.avia_accident]"
    reqs_data = [
        ("is empty", "", 500, FAIL),
        ("is made of spacechars", generate_random_key_space_chars(), 500, FAIL),
        ("is missing", None, 500, FAIL),
        ("is zero", "0", 500, FAIL),
        ("= False", "false", 500, FAIL),
        ("= True", "true", 500, FAIL),
        ("is garbage", generate_garbage_string(), 500, FAIL),
        ("is symbolic garbage", generate_garbage_of_symbolic_string(), 500, FAIL),
        ("is fractional number with dot", generate_random_string_as_number_fractional(),  200, PASS),
        ("is fractional number with comma", generate_random_string_as_number_fractional(comma_separation=True), 500, FAIL),
        ("has wrong format", "AB45", 500, FAIL),
        ("is negative", generate_random_string_as_number(negative=True), 500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(params_price_imputed_avia_accident=value, imputed_avia_accident="true"),
                 response, expected)
                for description, value, response, expected in reqs_data]
    req_list.append(("%s is correct, but [imputed.avia_accident] = False" % param_name,
                     construct_tickets_api_request(params_price_imputed_avia_accident="2000",
                                               imputed_avia_accident="false"),
                     200, PASS))
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[Params][Price][imputed.Delay_Dock]'")
def tickets_api_calc_params_price_imputed_delay_dock():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Params][Price][Imputed.Delay_Dock] and responses from API for different values
    """
    param_name = "[params][price][imputed.delay_dock]"
    reqs_data = [
        ("is empty", "", 500, FAIL),
        ("is made of spacechars", generate_random_key_space_chars(), 500, FAIL),
        ("is missing", None, 500, FAIL),
        ("is zero", "0", 500, FAIL),
        ("= False", "false", 500, FAIL),
        ("= True", "true", 500, FAIL),
        ("is garbage", generate_garbage_string(), 500, FAIL),
        ("is symbolic garbage", generate_garbage_of_symbolic_string(), 500, FAIL),
        ("is fractional number with dot", generate_random_string_as_number_fractional(), 200, PASS),
        ("is fractional number with comma", generate_random_string_as_number_fractional(comma_separation=True), 500, FAIL),
        ("has wrong format", "AB45", 500, FAIL),
        ("is negative", generate_random_string_as_number(negative=True), 500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(params_price_imputed_delay_dock=value, imputed_delay_dock="true"),
                 response, expected)
                for description, value, response, expected in reqs_data]
    req_list.append(("%s is correct, but [imputed.delay_dock] = False" % param_name,
                     construct_tickets_api_request(params_price_imputed_delay_dock=2000, imputed_delay_dock="false"),
                     200, PASS))
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter 'Action'")
def tickets_api_calc_action():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of Action parameter and responses from API for different values
    """
    param_name = "Action"
    reqs_data = [
        ("is correct", "new", 200, PASS),
        ("is empty", "", 500, PASS),
        ("is made of spacechars", generate_random_key_space_chars(), 500, PASS),
        ("is missing", None, 500, PASS),
        ("is zero", '0', 500, PASS),
        ("is garbage", generate_garbage_string(), 500, PASS),
        ("is symbolic garbage", generate_garbage_of_symbolic_string(), 500, PASS),
        ("is made of digits", generate_random_string_as_number(), 500, PASS),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(action=value), response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter 'Method'")
def tickets_api_calc_method():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of Method parameter and responses from API for different values
    """
    param_name = "Method"
    reqs_data = [
        ("is correct", "imputed", 200, FAIL),
        ("is empty", "", 500, PASS),
        ("is made of spacechars", generate_random_key_space_chars(), 500, PASS),
        ("is missing", None, 500, PASS),
        ("is zero", '0', 500, PASS),
        ("is garbage", generate_garbage_string(), 500, PASS),
        ("is symbolic garbage", generate_garbage_of_symbolic_string(), 500, PASS),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(action=value), response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[Tourists][Birthdate]'")
def tickets_api_calc_tourists_birthdate():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Tourists][BirthDate] parameter and responses from API for different values
    """
    param_name = "[Tourists][BirthDate]"
    # birthdate used in calculations is 20 years ago
    temp_birthdate = datetime.date.today() - relativedelta(years=20)
    reqs_data = [
        ('is empty', '', 200, PASS),
        ('is made of spacechars', generate_random_key_space_chars(), 200, FAIL),
        ('is missing', None, 200, FAIL),
        ('is zero', '0', 500, PASS),

        ('has garbage on the left', generate_garbage_string() + cfg_tourist_birthday, 500, FAIL),
        ('has garbage on the right', cfg_tourist_birthday + generate_garbage_string(), 500, PASS),
        ('has extra time on the left', '05:37:21 ' + cfg_tourist_birthday, 500, FAIL),
        ('has extra time on the right', cfg_tourist_birthday + ' 05:37:21', 500, FAIL),

        ('has wrong year position', temp_birthdate.strftime('%Y.%d.%m'), 500, FAIL),
        ('has wrong format (no day/month)', temp_birthdate.strftime('%m.%Y'), 500, PASS),
        ('has wrong format (no day, no month)', temp_birthdate.strftime('%Y'), 500, FAIL),
        ('has wrong format (no year)', temp_birthdate.strftime('%d.%m'), 500, FAIL),
        ('has wrong format (year of two digits)', temp_birthdate.strftime('%d.%m.%y'), 500, FAIL),
        ('has wrong format (slashes in date)', temp_birthdate.strftime('%d/%m/%Y'), 500, FAIL),

        ('has wrong format (too large day)', temp_birthdate.strftime('32.%m.%Y'), 500, PASS),
        ('has wrong format (day is out of format)', temp_birthdate.strftime('1A.%m.%Y'), 500, PASS),
        ('has wrong format (zero day)', temp_birthdate.strftime('00.%m.%Y'), 500, FAIL),

        ('has wrong format (too large month)', temp_birthdate.strftime('%d.13.%Y'), 500, PASS),
        ('has wrong format (month is out of format)', temp_birthdate.strftime('%d.0A.%Y'), 500, FAIL),
        ('has wrong format (zero month)', temp_birthdate.strftime('%d.00.%Y'), 500, FAIL),

        ('has wrong format (too large year)', temp_birthdate.strftime('%d.%m.5000'), 200, PASS),
        ('has wrong format (year is out of format)', temp_birthdate.strftime('%d.%m.20B5'), 500, PASS),
        ('has wrong format (zero year)', temp_birthdate.strftime('%d.%m.0000'), 500, FAIL),

        ('is today', (datetime.date.today()).strftime('%d.%m.%Y'), 500, FAIL),
        ('is tomorrow', (datetime.date.today() + datetime.timedelta(days=1)).strftime('%d.%m.%Y'), 500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(tourist_birthday=value), response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[Tourists][LastName]'")
def tickets_api_calc_tourists_last_name():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Tourists][LastName] parameter and responses from API for different values
    """
    param_name = "[Tourists][LastName]"
    reqs_data = [
        ("is empty", "", 500, FAIL),
        ("is made of spacechars", generate_random_key_space_chars(), 500, FAIL),
        ("is missing", None, 500, PASS),
        ("is zero", "0", 500, FAIL),
        ("is made of single char", generate_random_key_space_chars(), 200, PASS),
        ("is made of digits", generate_random_string_as_number(), 500, FAIL),
        ("is in capitals", cfg_tourist_lastname.upper(), 200, PASS),
        ("is cyrillic", "Бендер", 200, PASS),
        ("is cyrillic in capitals ", "БЕНДЕР", 200, PASS),
        ("has hyphen", "Bender-Zadunaiskiy", 200, PASS),
        ("has space", "Bender Zadunaiskiy", 200, PASS),
        ("has dot", "Bender.Zadunaiskiy", 500, FAIL),
        ("has symbolic garbage", cfg_tourist_lastname + generate_garbage_of_symbolic_string(), 500, FAIL),
        ("has punctuation marks",
            generate_garbage_punctuation_string() + cfg_tourist_lastname + generate_garbage_punctuation_string(),
            500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(tourist_lastname=value), response, expected)
                for description, value, response, expected in reqs_data]
    additional_tourist = [{"firstname": "Oleg", "lastname": "Artemov", "birthday": "07.11.1976"}]
    req_list.append(("is list of 2 persons",
                     construct_tickets_api_request(tourist_list=additional_tourist, tourists=2), 200, PASS))
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[Tourists][FirstName]'")
def tickets_api_calc_tourists_first_name():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Tourists][FirstName] parameter and responses from API for different values
    """
    param_name = "[Tourists][FirstName]"
    reqs_data = [
        ("is empty", "", 500, FAIL),
        ("is made of spacechars", generate_random_key_space_chars(), 500, FAIL),
        ("is missing", None, 500, PASS),
        ("is zero", "0", 500, FAIL),
        ("is made of single char", generate_single_char_random_string(), 200, PASS),
        ("is made of digits", generate_random_string_as_number(), 500, FAIL),
        ("is in capitals", cfg_buyer_firstname.upper(), 200, PASS),
        ("is cyrillic", "Остап", 200, PASS),
        ("is cyrillic in capitals ", "ОСТАП", 200, PASS),
        ("has hyphen", "Erich-Maria", 200, PASS),
        ("has space", "Erich Maria", 200, PASS),
        ("has dot", "Erich M.", 200, PASS),
        ("has symbolic garbage", cfg_tourist_firstname + generate_garbage_of_symbolic_string(), 500, FAIL),
        ("has punctuation marks",
            generate_garbage_punctuation_string() + cfg_tourist_firstname + generate_garbage_punctuation_string(),
            500, FAIL)
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(tourist_firstname=value), response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[Buyer][Email]'")
def tickets_api_calc_buyer_email():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Buyer][Email] parameter and responses from API for different values
    """
    param_name = "[Buyer][Email]"
    reqs_data = [
        ("is empty", "", 500, FAIL),
        ("is made of spacechars", generate_random_key_space_chars(), 500, FAIL),
        ("is missing", None, 500, PASS),
        ("is zero", "0", 500, FAIL),
        ("is made of commercial at only", "@", 500, FAIL),
        ("has digits", "alexander_khokhlov" + generate_random_string_as_number() + "@cherehapa.ru", 200, PASS),
        ("has digits in domain", "alexander_khokhlov@cherehapa" + generate_random_string_as_number() + ".ru", 200, PASS),
        ("has underscore", "alexander_khokhlov@cherehapa.ru", 200, PASS),
        ("has cyrillic character", "alexander_khokhloФ@cherehapa.ru", 500, FAIL),
        ("is cyrillic", "александрхохлов@почта.рф", 500, FAIL),
        ("has special character",
            "alexander" + get_random_string(size=2, chars="~!#$^&+-=") + "khokhlov@cherehapa.ru", 500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(buyer_email=value), response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[Buyer][LastName]'")
def tickets_api_calc_buyer_last_name():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Buyer][LastName] parameter and responses from API for different values
    """
    param_name = "[Buyer][LastName]"
    reqs_data = [
        ("is empty", "", 500, FAIL),
        ("is made of spacechars", generate_random_key_space_chars(), 500, FAIL),
        ("is missing", None, 500, PASS),
        ("is zero", "0", 500, FAIL),
        ("is made of single char", generate_single_char_random_string(), 200, PASS),
        ("is made of digits", generate_random_string_as_number(), 500, FAIL),
        ("is in capitals", cfg_buyer_lastname.upper(), 200, PASS),
        ("is cyrillic", "Бендер", 200, PASS),
        ("is cyrillic in capitals ", "БЕНДЕР", 200, PASS),
        ("has hyphen", "Bender-Zadunaiskiy", 200, PASS),
        ("has space", "Bender Zadunaiskiy", 200, PASS),
        ("has dot", "Bender.Zadunaiskiy", 500, FAIL),
        ("has symbolic garbage", cfg_buyer_lastname + generate_garbage_of_symbolic_string(), 500, FAIL),
        ("has punctuation marks",
            generate_garbage_punctuation_string() + cfg_buyer_lastname + generate_garbage_punctuation_string(),
            500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(buyer_lastname=value), response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[Buyer][FirstName]'")
def tickets_api_calc_buyer_first_name():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of [Buyer][FirstName] parameter and responses from API for different values
    """
    param_name = "[Buyer][FirstName]"
    reqs_data = [
        ("is empty", "", 500, FAIL),
        ("is made of spacechars", generate_random_key_space_chars(), 500, FAIL),
        ("is missing", None, 500, PASS),
        ("is zero", "0", 500, FAIL),
        ("is made of single char", generate_single_char_random_string(), 200, PASS),
        ("is made of digits", generate_random_string_as_number(), 500, FAIL),
        ("is in capitals", cfg_buyer_firstname.upper(), 200, PASS),
        ("is cyrillic", "Остап", 200, PASS),
        ("is cyrillic in capitals ", "ОСТАП", 200, PASS),
        ("has hyphen", "Erich-Maria", 200, PASS),
        ("has space", "Erich Maria", 200, PASS),
        ("has dot", "Erich M.", 200, PASS),
        ("has symbolic garbage", cfg_buyer_firstname + generate_garbage_of_symbolic_string(), 500, FAIL),
        ("has punctuation marks",
            generate_garbage_punctuation_string() + cfg_buyer_firstname + generate_garbage_punctuation_string(),
            500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(buyer_firstname=value), response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


@che_test_case(tc_prefix + "parameter '[Buyer][RefId]'")
def tickets_api_calc_ref_id():
    """TestCase: Requests via API endpoint the tickets policy calculation and validate
    the values of RefId parameter and responses from API for different values
    """
    param_name = "RefId"
    reqs_data = [
        ("is missing", None, 500, FAIL),
        ("is empty", "", 500, FAIL),
        ("is made of spacechars", generate_random_key_space_chars(), 500, FAIL),
        ("is zero", '0', 500, FAIL),
        ("is negative", generate_random_string_as_number(negative=True), 500, FAIL),
        ("is not in valid format", 'A1', 500, FAIL),
        ("is string", 'AB', 500, FAIL),
        ("is fractional number with dot", generate_random_string_as_number_fractional(), 500, FAIL),
        ("is fractional number with comma",
            generate_random_string_as_number_fractional(comma_separation=True), 500, FAIL),
    ]
    req_list = [("%s %s" % (param_name, description),
                 construct_tickets_api_request(refid=value), response, expected)
                for description, value, response, expected in reqs_data]
    return execute_tickets_calculation_requests(req_list)


################################################################################
# main function
################################################################################
@che_autotest(__file__)
def test_tickets_api_calculation():
    """Test suite to verify the tickets API request for tickets insurance, its parameters and returned response.
    """
    test_cases = [
        tickets_api_calc_api_format,
        tickets_api_calc_key,
        tickets_api_calc_datestart,
        tickets_api_calc_dateend,
        tickets_api_calc_company,
        tickets_api_calc_tourists,
        tickets_api_calc_imputed_avia_cargo,
        tickets_api_calc_imputed_delay_regular,
        tickets_api_calc_imputed_cancel_travel,
        tickets_api_calc_imputed_avia_accident,
        tickets_api_calc_imputed_delay_dock,
        tickets_api_calc_params_price_imputed_avia_cargo,
        tickets_api_calc_params_price_imputed_delay_regular,
        tickets_api_calc_params_price_imputed_cancel_travel,
        tickets_api_calc_params_price_imputed_avia_accident,
        tickets_api_calc_params_price_imputed_delay_dock,
        tickets_api_calc_action,
        tickets_api_calc_method,
        tickets_api_calc_tourists_birthdate,
        tickets_api_calc_tourists_last_name,
        tickets_api_calc_tourists_first_name,
        tickets_api_calc_buyer_email,
        tickets_api_calc_buyer_last_name,
        tickets_api_calc_buyer_first_name,
        tickets_api_calc_ref_id
    ]

    return run_test_and_get_result(test_cases)


if __name__ == '__main__':
    test_tickets_api_calculation()
