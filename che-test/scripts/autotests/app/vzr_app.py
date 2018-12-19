# -*- coding: utf-8; -*-
#
# Description: test suite to verify the process of policy creation using web
#              interface. Emulated payment from credit card.
#
import urllib.parse
from requests.exceptions import ConnectionError
from selenium.common.exceptions import WebDriverException

from model.vzr_policy import Policy
from pages.vzr_calculator_page import CalculatorPage
from pages.vzr_cherehapa_main_page import CherehapaMainPage
from pages.vzr_final_page import FinalPage
from pages.vzr_insurance_page import InsurancePage
from pages.vzr_insurance_search_page import InsuranceSearchPage
from pages.vzr_payment_page import PaymentPage
from pages.vzr_policy_creation_animated_page import PolicyCreationAnimatedPage
from common.webpages.pageobject import PageObject, PageError

import common.config_module as config_module
import common.logger as logger
from common.browser import Browser
from common.database import CheDb
from common.mail_helper import MailHelper
from common.system import resolve_domain_names_reachability, wait_and_count, make_target_url


class CheWebVzrApplication:
    _email_service_was_tested = False

    def __init__(self, config=None):
        if config:
            self.config = config
        else:
            self.config = config_module.load(config_module.get_dir_by_suffix("che-test/scripts/autotests/config/env.json"))
        self.policy_data = Policy()
        self.url_params = dict()

        # environment options
        self.testing_url = make_target_url()
        self.make_screenshots = self.config["environment"]["make_screenshots"]
        self.webdriver = None

    def __del__(self):
        if self.webdriver is None:
            return
        self.webdriver.quit()
        self.webdriver = None

    def __enter__(self):
        # This method redefinition is required according to the PEP 343 to use the class in 'with .. as' constructions
        return self

    def __exit__(self, ttype, value, traceback):
        # This method redefinition is required according to the PEP 343 to use the class in 'with .. as' constructions
        self.__del__()

    def destroy(self):
        self.__del__()

    def set_url_params(self, params):
        assert isinstance(params, dict)
        self.url_params.update(params)
        self.append_params_to_url()

    def delete_url_param(self, param):
        if self.url_params.get(param):
            self.url_params.pop(param)
        self.append_params_to_url()

    def reset_url_params(self):
        self.url_params = dict()
        self.append_params_to_url()

    def append_params_to_url(self):
        self.testing_url = "?".join([make_target_url(), urllib.parse.urlencode(self.url_params)])

    def prepare_driver_and_pages(self):
        self.webdriver = Browser().run(self.config["environment"]["browser"])
        # pages to go through policy creation
        self.main_page = CherehapaMainPage(self)
        self.insurance_search_page = InsuranceSearchPage(self)
        self.calculator_page = CalculatorPage(self)
        self.insurance_page = InsurancePage(self)
        self.payment_details_page = PaymentPage(self)
        self.policy_creation_animated_page = PolicyCreationAnimatedPage(self)
        self.final_readyness_page = FinalPage(self)

    def create_and_buy_policy(self, given_policy_data):
        with CheDb(db_config=config_module.load()["database"], verbose=False) as db:
            selected_insurance_company = db.get_insurance_companies_list()[given_policy_data["company"]]
        tc_name = "---- Processing policy #%s for '%s'" \
                  % (given_policy_data["id"], selected_insurance_company)
        logger.start(tc_name)

        self.prepare_driver_and_pages()
        self.policy_data.set_policy_default_values()
        self.policy_data.load_values_from_structure(given_policy_data)

        try:
            self.main_page.open_main_cherehapa_page()
            self.main_page.set_country_to_travel(self.policy_data.country_to_travel)
            self.main_page.set_country_group_to_travel(self.policy_data.country_group_to_travel)
            self.main_page.set_travel_start_date(self.policy_data.date_start.strftime("%d.%m.%Y"))
            self.main_page.set_travel_end_date(self.policy_data.date_end.strftime("%d.%m.%Y"))
            self.main_page.set_travellers_age(self.policy_data.traveller_ages_list)
            buy_policy_result = self.main_page.start_insurance_search()

            buy_policy_result = self.insurance_search_page.wait_and_check_insurance_search_page() and buy_policy_result

            self.calculator_page.wait_for_calculator_page()
            if self.policy_data.cashless_payment:
                self.calculator_page.login_to_personal_cabinet(".offer-buy")
            self.calculator_page.set_policy_options(self.policy_data)
            buy_policy_result = self.calculator_page.buy_insurance_from_company(self.policy_data.company,
                                                                                self.policy_data.expected_calculation) \
                                and buy_policy_result
            if self.calculator_page.completeness:
                # policy was calculated unexpectedly or no policy was calculated
                if bool(buy_policy_result):
                    logger.finishSuccess(tc_name)
                else:
                    logger.finishFail(tc_name)
                logger.print_empty_line()
                return buy_policy_result

            self.insurance_page.wait_for_policy_details_page()
            self.insurance_page.set_travellers_data(self.policy_data.traveller_list)
            self.insurance_page.set_buyer_data(self.policy_data.buyer)
            self.insurance_page.compare_price_expected_and_actual(self.policy_data.price)
            buy_policy_result = self.insurance_page.continue_operation_to_payment() and buy_policy_result

            self.payment_details_page.wait_for_payment_details_page()
            self.payment_details_page.set_credit_card_data(self.policy_data.banking_card)
            self.policy_data.price = self.payment_details_page.get_price_of_policy_from_page()
            self.payment_details_page.compare_price_expected_and_actual(self.policy_data.price)
            buy_policy_result = self.payment_details_page.pay_for_policy() and buy_policy_result

            mail_checker = MailHelper(self)

            self.policy_creation_animated_page.wait_for_policy_creation_page()
            buy_policy_result = self.policy_creation_animated_page.get_task_id() and buy_policy_result

            buy_policy_result = self.final_readyness_page.wait_for_final_page() and buy_policy_result

            with CheDb(db_config=config_module.load()["database"], verbose=False) as db:
                buy_policy_result = db.verify_policy_data_in_database_by_task_id(self.policy_data.task_id,
                                                                                 self.policy_data.price,
                                                                                 self.policy_data.check_parent_task_only) \
                                    and buy_policy_result
                if bool(self.policy_data.cashless_payment):
                    buy_policy_result = db.verify_policies_payment_system_by_task_id(self.policy_data.task_id,
                                                                                     "wire",
                                                                                     self.policy_data.check_parent_task_only) \
                                        and buy_policy_result

            buy_policy_result = mail_checker.check_email_matches_expected_format_and_contents() and buy_policy_result

            if bool(buy_policy_result):
                logger.finishSuccess(tc_name)
            else:
                logger.finishFail(tc_name)
            logger.print_empty_line()
            return buy_policy_result

        except (PageError, ConnectionError) as e:
            logger.error("Error detected (%s): %s" % (e.__class__, e))
            domains_can_be_resolved = resolve_domain_names_reachability()
            logger.print_empty_line()
            logger.finishFail(tc_name)
            if not domains_can_be_resolved:
                logger.error("Connection problems, sleep for 5 minutes")
                wait_and_count(300)
                resolve_domain_names_reachability()
                logger.print_empty_line()
            return False
        except WebDriverException as e:
            logger.error("WebDriver error. %s" % e)
            PageObject(self).make_screenshot("web_driver_error")
            self.webdriver.quit()
            self.webdriver = None
            logger.print_empty_line()
            logger.finishFail(tc_name)
            raise
        except (KeyboardInterrupt, Exception) as e:
            logger.error("Error detected (%s): %s" % (e.__class__, e))
            logger.print_empty_line()
            logger.finishFail(tc_name)
            raise

    @classmethod
    def is_email_service_tested(cls):
        is_email_service_tested = cls._email_service_was_tested
        msg = "Email service was checked within test execution"
        logger.success(msg) if is_email_service_tested else logger.fail(msg)
        return is_email_service_tested

    @classmethod
    def set_email_service_tested(cls, value=True):
        cls._email_service_was_tested = value
