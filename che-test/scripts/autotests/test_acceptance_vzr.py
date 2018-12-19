#!/usr/bin/env python3
# -*- coding: utf-8; -*-
#
# Description: test suite to verify the process of policy creation using web
#              interface. Emulated payment by credit card.
#
import os
from app.vzr_app import CheWebVzrApplication
from model.vzr_rules import PolicyRulesGenerator
import common.config_module as config_module
import common.logger as logger
from common.currency import request_currency
from common.database import CheDb
from common.system import che_autotest


@che_autotest(__file__)
def test_acceptance():
    overall_result = request_currency(verbose=True)
    prepare_screenshots_catalog()
    policies_list = PolicyRulesGenerator().generate_policy_data_list()
    overall_result = bool(policies_list) and overall_result

    processed_companies = []
    for policy in policies_list:
        with CheWebVzrApplication() as app:
            single_result = app.create_and_buy_policy(policy)
            processed_companies.append((policy["company"], policy["id"], single_result))
            overall_result = single_result and overall_result

    overall_result = CheWebVzrApplication.is_email_service_tested() and overall_result

    with CheDb(db_config=config_module.load()["database"], verbose=False) as db:
        disabled_companies = db.get_insurance_companies_list(disabled=1)
        all_companies = db.get_insurance_companies_list()

    logger.success("Processed {n:d} scenarios".format(n=len(processed_companies)))
    for company in processed_companies:
        logger.info("    '%s' scenario #%s: %s" % (all_companies[company[0]], company[1], "ok" if company[2] else "Failed"))
    logger.info("    Scenarios Passed: %s" % sum([x[2] for x in processed_companies]))
    logger.info("    Scenarios Failed: %s" % sum([not x[2] for x in processed_companies]))
    logger.warning("Disabled companies: {0}".format(
        ", ".join([all_companies[k] for k in list(filter(lambda key: key in disabled_companies, all_companies.keys()))])))
    return overall_result


def prepare_screenshots_catalog():
    config_dir = config_module.get_dir_by_suffix("che-test/scripts/autotests/config/pageobjects.json")
    screenshots_catalog_name = config_module.get_value_from_config("['path']['screenshot_catalog']", config_dir)
    screenshot_catalog = config_module.get_dir_by_suffix("che-test/scripts/autotests/" + screenshots_catalog_name)
    if not os.path.exists(screenshot_catalog):
        os.mkdir(screenshot_catalog)
    for file in os.listdir(screenshot_catalog):
        os.remove(os.path.join(screenshot_catalog, file))


if __name__ == "__main__":
    test_acceptance()
