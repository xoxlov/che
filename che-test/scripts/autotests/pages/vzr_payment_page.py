# -*- coding: utf-8; -*-
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select

from common.webpages.pageobject import PageObject
from common.webpages.pageobject import page_element_operation
import common.logger as logger
from common.config_module import get_value_from_config


class PaymentPage(PageObject):

    def __init__(self, app):
        super(PaymentPage, self).__init__(app)
        self.page_name = "Payment Details page"
        self.screenshot_name_suffix = "payment_page"
        self.payment_page_timeout = int(get_value_from_config("['vzr_pages']['payment_page_timeout']", self.config_file_name))
        self.expected_titles = ["Заполнение данных страхового полиса", "Заполнение платежных данных"]

    @property
    def card_number(self):
        found = self.driver.find_elements_by_css_selector("input[name='card_number']")
        return found[0] if found else None

    @property
    def card_month(self):
        found = self.driver.find_elements_by_css_selector("input[name='card_month']")
        return found[0] if found else None

    @property
    def card_year(self):
        found = self.driver.find_elements_by_css_selector("input[name='card_year']")
        return found[0] if found else None

    @property
    def card_cvv(self):
        found = self.driver.find_elements_by_css_selector("input[name='card_cvv']")
        return found[0] if found else None

    @property
    def card_holder(self):
        found = self.driver.find_elements_by_css_selector("input[name='card_holder']")
        return found[0] if found else None

    @property
    def price_from_page(self):
        found = self.driver.find_elements_by_id("price")
        return float(found[0].get_property("dataset")["number"]) if found else None

    @property
    def insurance_card_payment_button(self):
        found = self.driver.find_elements_by_css_selector("div#card button.large")
        return found[0] if found else None

    @property
    def insurance_wire_payment_button(self):
        found = self.driver.find_elements_by_css_selector("div#wire button.large")
        return found[0] if found else None

    def wait_for_payment_details_page(self):
        logger.start(self.page_name)
        try:
            WebDriverWait(self.driver, self.payment_page_timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".btn_successCard")))
            self.result = self.verify_page_title(verbose=True)
        except TimeoutException:
            self.result = False

    @page_element_operation
    def set_credit_card_data(self, card):
        self.type_data_to_input(self.card_number, card.number)
        self.type_data_to_input(self.card_month, card.month)
        self.type_data_to_input(self.card_year, card.year)
        self.type_data_to_input(self.card_holder, card.holder)
        self.type_data_to_input(self.card_cvv, card.cvv)
        logger.success("Card data are set successfully")

    @page_element_operation
    def get_price_of_policy_from_page(self):
        price = self.price_from_page
        if price:
            logger.success("Policy price calculated = %.2f" % price)
        else:
            logger.fail("Policy price is found on the page")
        return price or 0.0

    @page_element_operation
    def compare_price_expected_and_actual(self, expected_price_rub):
        displayed_price = self.price_from_page
        if displayed_price == expected_price_rub:
            logger.success("Policy price displayed (%.2f) matches expected (%.2f)" % (displayed_price, expected_price_rub))
        else:
            self.result = False
            logger.fail("Policy price displayed (%.2f) matches expected (%.2f)" % (displayed_price, expected_price_rub))

    @page_element_operation
    def pay_for_policy(self):
        self.make_screenshot_if_needed(suffix=self.screenshot_name_suffix + "_ready")
        if self.app.policy_data.cashless_payment:
            self.select_cashless_payment()
            self.insurance_wire_payment_button.click()
            logger.success("Cashless payment selected")
        else:
            self.insurance_card_payment_button.click()
            logger.success("Payment with card selected")
        return self.get_page_result()

    def select_cashless_payment(self):
        payment_dropdown_list = Select(self.driver.find_element_by_css_selector("select.payment_method"))
        payment_dropdown_list.select_by_value("wire")
