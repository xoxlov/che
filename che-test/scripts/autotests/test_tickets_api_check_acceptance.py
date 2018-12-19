#!/usr/bin/env python3
# -*- coding: utf-8; -*-
import datetime
from dateutil.relativedelta import relativedelta

from common.system import che_autotest, che_test_case, run_test_and_get_result
from common.tickets_api import execute_tickets_api_policy_creation
from common.config_module import load


###############################################################################
# Config values and constants
###############################################################################
TC_PREFIX = "Tickets API policy processing request "
config = load("config/tickets.json")
cfg_tourist_birthday = config[u'tourist_birthday']
cfg_tourist_lastname = config[u'tourist_lastname']
cfg_tourist_firstname = config[u'tourist_firstname']
cfg_buyer_email = config[u'buyer_email']
cfg_buyer_lastname = config[u'buyer_lastname']
cfg_buyer_firstname = config[u'buyer_firstname']


###############################################################################
# Functions implementing Test Cases
###############################################################################
@che_test_case(TC_PREFIX + "Sample Request")
def tickets_api_case_sample():
    """Request via API the tickets policy creation and validate the policy creation process.
    The request is based for set of three included options.
    """
    # set tourist's birthday about 25 years ago
    tourist_birthday = (datetime.date.today() - relativedelta(years=27)).strftime('02.01.%Y')
    # set trip dates to the next month
    date_start = (datetime.date.today() + relativedelta(months=1)).strftime('01.%m.%Y')
    date_end = (datetime.date.today() + relativedelta(months=1)).strftime('10.%m.%Y')

    params = {"imputed_avia_cargo": "true",
              "imputed_avia_accident": "true",
              "imputed_delay_dock": "true",
              "params_price_imputed_avia_cargo": 19101,
              "params_price_imputed_avia_accident": 19101,
              "params_price_imputed_delay_dock": 10000,
              "tourist_birthday": tourist_birthday,
              "date_start": date_start,
              "date_end": date_end}
    return execute_tickets_api_policy_creation("Sample Request", **params)


@che_test_case(TC_PREFIX + "Single Risk (Avia Cargo)")
def tickets_api_case_single_risk_avia_cargo():
    """Request via API the tickets policy creation and validate the policy creation process.
    The request tests single risk for Avia Cargo option.
    """
    # set tourist's birthday over 60 years ago
    tourist_birthday = (datetime.date.today() - relativedelta(years=66)).strftime('10.12.%Y')
    # set trip dates to the next month
    date_start = (datetime.date.today() + relativedelta(months=1)).strftime('22.%m.%Y')
    date_end = (datetime.date.today() + relativedelta(months=1)).strftime('28.%m.%Y')

    params = {"tourist_birthday": tourist_birthday,
              "tourist_lastname": cfg_tourist_lastname,
              "tourist_firstname": cfg_tourist_firstname,
              "buyer_email": cfg_buyer_email,
              "buyer_lastname": cfg_buyer_lastname,
              "buyer_firstname": cfg_buyer_firstname,
              "imputed_avia_cargo": "true",
              "params_price_imputed_avia_cargo": 80000,
              "date_start": date_start,
              "date_end": date_end}
    return execute_tickets_api_policy_creation("Single Risk (Avia Cargo)", **params)


@che_test_case(TC_PREFIX + "Single Risk (Avia Accident)")
def tickets_api_case_single_risk_avia_accident():
    """Request via API the tickets policy creation and validate the policy creation process.
    The request tests single risk for Avia Accident option.
    """
    # set tourist's birthday over 60 years ago
    tourist_birthday = (datetime.date.today() - relativedelta(years=66)).strftime('10.12.%Y')
    # set trip dates to the next month
    date_start = (datetime.date.today() + relativedelta(months=1)).strftime('22.%m.%Y')
    date_end = (datetime.date.today() + relativedelta(months=1)).strftime('28.%m.%Y')

    params = {"tourist_birthday": tourist_birthday,
              "tourist_lastname": cfg_tourist_lastname,
              "tourist_firstname": cfg_tourist_firstname,
              "buyer_email": cfg_buyer_email,
              "buyer_lastname": cfg_buyer_lastname,
              "buyer_firstname": cfg_buyer_firstname,
              "imputed_avia_accident": "true",
              "params_price_imputed_avia_accident": 80000,
              "date_start": date_start,
              "date_end": date_end}
    return execute_tickets_api_policy_creation("Single Risk (Avia Accident)", **params)


@che_test_case(TC_PREFIX + "Single Risk (Cancel Travel)")
def tickets_api_case_single_risk_cancel_travel():
    """Request via API the tickets policy creation and validate the policy creation process.
    The request tests single risk for Cancel Travel option.
    """
    # set tourist's birthday over 60 years ago
    tourist_birthday = (datetime.date.today() - relativedelta(years=66)).strftime('10.12.%Y')
    # set trip dates to the next month
    date_start = (datetime.date.today() + relativedelta(months=1)).strftime('22.%m.%Y')
    date_end = (datetime.date.today() + relativedelta(months=1)).strftime('28.%m.%Y')

    params = {"tourist_birthday": tourist_birthday,
              "tourist_lastname": cfg_tourist_lastname,
              "tourist_firstname": cfg_tourist_firstname,
              "buyer_email": cfg_buyer_email,
              "buyer_lastname": cfg_buyer_lastname,
              "buyer_firstname": cfg_buyer_firstname,
              "imputed_cancel_travel": "true",
              "params_price_imputed_cancel_travel": 80000,
              "date_start": date_start,
              "date_end": date_end}
    return execute_tickets_api_policy_creation("Single Risk (Cancel Travel)", **params)


@che_test_case(TC_PREFIX + "Single Risk (Delay Dock)")
def tickets_api_case_single_risk_delay_dock():
    """Request via API the tickets policy creation and validate the policy creation process.
    The request tests single risk for Delay Dock option.
    """
    # set tourist's birthday over 60 years ago
    tourist_birthday = (datetime.date.today() - relativedelta(years=66)).strftime('10.12.%Y')
    # set trip dates to the next month
    date_start = (datetime.date.today() + relativedelta(months=1)).strftime('22.%m.%Y')
    date_end = (datetime.date.today() + relativedelta(months=1)).strftime('28.%m.%Y')

    params = {"tourist_birthday": tourist_birthday,
              "tourist_lastname": cfg_tourist_lastname,
              "tourist_firstname": cfg_tourist_firstname,
              "buyer_email": cfg_buyer_email,
              "buyer_lastname": cfg_buyer_lastname,
              "buyer_firstname": cfg_buyer_firstname,
              "imputed_delay_dock": "true",
              "params_price_imputed_delay_dock": 80000,
              "date_start": date_start,
              "date_end": date_end}
    return execute_tickets_api_policy_creation("Single Risk (Delay Dock)", **params)


@che_test_case(TC_PREFIX + "Single Risk (Delay Regular)")
def tickets_api_case_single_risk_delay_regular():
    """Request via API the tickets policy creation and validate the policy creation process.
    The request tests single risk for Delay Regular option.
    """
    # set tourist's birthday over 60 years ago
    tourist_birthday = (datetime.date.today() - relativedelta(years=66)).strftime('10.12.%Y')
    # set trip dates to the next month
    date_start = (datetime.date.today() + relativedelta(months=1)).strftime('22.%m.%Y')
    date_end = (datetime.date.today() + relativedelta(months=1)).strftime('28.%m.%Y')

    params = {"tourist_birthday": tourist_birthday,
              "tourist_lastname": cfg_tourist_lastname,
              "tourist_firstname": cfg_tourist_firstname,
              "buyer_email": cfg_buyer_email,
              "buyer_lastname": cfg_buyer_lastname,
              "buyer_firstname": cfg_buyer_firstname,
              "imputed_delay_regular": "true",
              "params_price_imputed_delay_regular": 80000,
              "date_start": date_start,
              "date_end": date_end}
    return execute_tickets_api_policy_creation("Single Risk (Delay Regular)", **params)


@che_test_case(TC_PREFIX + "Multiple Options")
def tickets_api_case_multiple_options():
    """Request via API the tickets policy creation and validate the policy creation process.
    The request tests multiple risks.
    """
    # set tourist's birthday about 25 years ago
    tourist_birthday = (datetime.date.today() - relativedelta(years=25)).strftime('01.01.%Y')
    # set trip for 3 months
    date_start = (datetime.date.today() + relativedelta(months=1)).strftime('20.%m.%Y')
    date_end = (datetime.date.today() + relativedelta(months=4)).strftime('21.%m.%Y')

    params = {"tourist_birthday": tourist_birthday,
              "tourist_lastname": cfg_tourist_lastname,
              "tourist_firstname": cfg_tourist_firstname,
              "buyer_email": cfg_buyer_email,
              "buyer_lastname": cfg_buyer_lastname,
              "buyer_firstname": cfg_buyer_firstname,
              "imputed_avia_cargo": "true",
              "imputed_avia_accident": "true",
              "imputed_cancel_travel": "true",
              "imputed_delay_dock": "true",
              "imputed_delay_regular": "true",
              "params_price_imputed_avia_cargo": 10000,
              "params_price_imputed_avia_accident": 10000,
              "params_price_imputed_cancel_travel": 10000,
              "params_price_imputed_delay_dock": 10000,
              "params_price_imputed_delay_regular": 10000,
              "date_start": date_start,
              "date_end": date_end}
    return execute_tickets_api_policy_creation("Multiple Options", **params)


@che_test_case(TC_PREFIX + "Multiple Tourists")
def tickets_api_case_multiple_tourists():
    """Request via API the tickets policy creation and validate the policy creation process.
    The request tests single risk for group of tourists.
    """
    # set trip dates to the next month
    date_start = (datetime.date.today() + relativedelta(months=1)).strftime('01.%m.%Y')
    date_end = (datetime.date.today() + relativedelta(months=1)).strftime('10.%m.%Y')
    # set tourists list except first one
    tourist_list = [
        {"firstname": "Testik", "lastname": "Testov", "birthday": "12.12.1986"},
        {"firstname": "Test", "lastname": "Testovii", "birthday": "01.01.1990"},
        {"firstname": "Testta", "lastname": "Testovaya", "birthday": "12.12.1986"},
        {"firstname": "Testo", "lastname": "Testovoe", "birthday": "12.12.1986"}
    ]
    params = {"tourist_birthday": cfg_tourist_birthday,
              "tourist_lastname": cfg_tourist_lastname,
              "tourist_firstname": cfg_tourist_firstname,
              "tourists": 5,
              "buyer_email": cfg_buyer_email,
              "buyer_lastname": cfg_buyer_lastname,
              "buyer_firstname": cfg_buyer_firstname,
              "imputed_avia_accident": "true",
              "params_price_imputed_avia_accident": 10000,
              "date_start": date_start,
              "date_end": date_end}
    return execute_tickets_api_policy_creation("Multiple Tourists", tourist_list=tourist_list, **params)


@che_test_case(TC_PREFIX + "Multiple Options and Tourists")
def tickets_api_case_multiple_options_tourists():
    """Request via API the tickets policy creation and validate the policy creation process.
    The request tests multiple risks for group of tourists.
    """
    # set trip for 3 months
    date_start = (datetime.date.today() + relativedelta(months=1)).strftime('20.%m.%Y')
    date_end = (datetime.date.today() + relativedelta(months=4)).strftime('21.%m.%Y')
    # set tourists list except first one
    tourist_list = [
        {"firstname": "Testik", "lastname": "Testov", "birthday": "12.12.1986"},
        {"firstname": "Test", "lastname": "Testovii", "birthday": "01.01.1990"},
        {"firstname": "Testta", "lastname": "Testovaya", "birthday": "12.12.1986"},
        {"firstname": "Testo", "lastname": "Testovoe", "birthday": "12.12.1986"}
    ]
    params = {"tourist_birthday": cfg_tourist_birthday,
              "tourist_lastname": cfg_tourist_lastname,
              "tourist_firstname": cfg_tourist_firstname,
              "tourists": 5,
              "buyer_email": cfg_buyer_email,
              "buyer_lastname": cfg_buyer_lastname,
              "buyer_firstname": cfg_buyer_firstname,
              "imputed_avia_cargo": "true",
              "imputed_avia_accident": "true",
              "imputed_cancel_travel": "true",
              "imputed_delay_dock": "true",
              "imputed_delay_regular": "true",
              "params_price_imputed_avia_cargo": 10000,
              "params_price_imputed_avia_accident": 10000,
              "params_price_imputed_cancel_travel": 10000,
              "params_price_imputed_delay_dock": 10000,
              "params_price_imputed_delay_regular": 10000,
              "date_start": date_start,
              "date_end": date_end}
    return execute_tickets_api_policy_creation("Multiple Options and Tourists", tourist_list=tourist_list, **params)


################################################################################
# main function
################################################################################
@che_autotest(__file__)
def test_tickets_api_acceptance():
    """Test suite to verify the tickets API in order to create the policy
    """
    test_cases = [
        tickets_api_case_sample,
        tickets_api_case_single_risk_avia_cargo,
        tickets_api_case_single_risk_avia_accident,
        tickets_api_case_single_risk_cancel_travel,
        tickets_api_case_single_risk_delay_dock,
        tickets_api_case_single_risk_delay_regular,
        tickets_api_case_multiple_options,
        tickets_api_case_multiple_tourists,
        tickets_api_case_multiple_options_tourists,
    ]
    return run_test_and_get_result(test_cases)


if __name__ == '__main__':
    test_tickets_api_acceptance()
