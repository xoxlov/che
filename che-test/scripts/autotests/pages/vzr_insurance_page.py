# -*- coding: utf-8; -*-
from common.webpages.pageobject import PageObject
from common.webpages.pageobject import page_element_operation
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import common.logger as logger
from common.config_module import get_value_from_config


class InsurancePage(PageObject):

    def __init__(self, app):
        super(InsurancePage, self).__init__(app)
        self.insurance_page_timeout = float(get_value_from_config("['vzr_pages']['insurance_page_timeout']", self.config_file_name))
        self.page_name = "Insurance page"
        self.screenshot_name_suffix = "insurance_page"
        self.expected_titles = [u"Заполнение данных страхового полиса".encode("utf-8"), u"Расчет стоимости страховки".encode("utf-8")]

    @property
    def add_another_traveller_button(self):
        found = self.driver.find_elements_by_css_selector("div.add-tr")
        return found[0] if found else None

    @property
    def buyer_birthday(self):
        found = self.driver.find_elements_by_css_selector(".buyer-info input.birthday-input")
        return found[0] if found else None

    @property
    def buyer_email(self):
        found = self.driver.find_elements_by_css_selector(".buyer-info input.email")
        return found[0] if found else None

    @property
    def buyer_first_name(self):
        found = self.driver.find_elements_by_css_selector(".buyer-info input.name")
        return found[0] if found else None

    @property
    def buyer_last_name(self):
        found = self.driver.find_elements_by_css_selector(".buyer-info input.surname")
        return found[0] if found else None

    @property
    def buyer_phone(self):
        found = self.driver.find_elements_by_css_selector(".buyer-info input.phone")
        return found[0] if found else None

    @property
    def buyer_second_name(self):
        found = self.driver.find_elements_by_css_selector(".buyer-info input.secondName")
        return found[0] if found else None

    @property
    def number_available_travellers(self):
        return len(self.driver.find_elements_by_css_selector(".travelers-info input[name='firstName']"))

    @property
    def price_changed_notification(self):
        try:
            WebDriverWait(self.driver, self.element_wait_timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".custom-pnotify")))
            return self.driver.find_element_by_css_selector(".custom-pnotify")
        except TimeoutException:
            return None

    def wait_price_changed_notification_away(self):
        try:
            WebDriverWait(self.driver, self.element_wait_timeout).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, ".custom-pnotify")))
            return True
        except TimeoutException:
            return False

    @property
    def price_from_page(self):
        found = self.driver.find_elements_by_css_selector("#price.odometer")
        return float(found[0].get_property("dataset")['number']) if found else None

    @property
    def submit_button(self):
        found = self.driver.find_elements_by_css_selector("#submitBtn")
        return found[0] if found else None

    @property
    def traveller_birthday(self):
        number = self.traveller_number or 0
        return self.driver.find_elements_by_css_selector(".travelers-info input.birthday-input")[number]

    @property
    def traveller_first_name(self):
        number = self.traveller_number or 0
        return self.driver.find_elements_by_css_selector(".travelers-info input[name='firstName']")[number]

    @property
    def traveller_last_name(self):
        number = self.traveller_number or 0
        return self.driver.find_elements_by_css_selector(".travelers-info input[name='lastName']")[number]

    def wait_for_policy_details_page(self):
        self.result = True
        logger.start(self.page_name)
        self.wait_for_page_to_be_loaded(self.insurance_page_timeout, By.CLASS_NAME, "birthday-input")
        logger.success("{page} was loaded successfully".format(page=self.page_name))

    def set_travellers_data(self, travellers_list):
        for number, traveller in list(enumerate(travellers_list)):
            if self.number_available_travellers < number:
                self.add_another_traveller_button.click()
            self.traveller_number = number
            self.set_traveller_first_name(traveller["traveller_first_name"])
            self.set_traveller_last_name(traveller["traveller_last_name"])
            logger.success("Traveller #{0} name set to '{1}'".format(number + 1, ' '.join([traveller["traveller_first_name"], traveller["traveller_last_name"]])))
            self.set_traveller_birthday(traveller["traveller_birthday"])
            logger.success("Traveller #{0} birthday set to '{1}'".format(number + 1, traveller["traveller_birthday"]))
            if self.price_changed_notification:
                self.wait_price_changed_notification_away()
                changed_price = self.price_from_page
                logger.warning("Warning! Policy price was changed from %s to %s" % (self.app.policy_data.price, changed_price))
                self.app.policy_data.price = changed_price

    @page_element_operation
    def set_traveller_first_name(self, name):
        if self.traveller_first_name:
            self.type_data_to_input(self.traveller_first_name, name)

    @page_element_operation
    def set_traveller_last_name(self, name):
        if self.traveller_last_name:
            self.type_data_to_input(self.traveller_last_name, name)

    @page_element_operation
    def set_traveller_birthday(self, day):
        if self.traveller_birthday:
            self.type_data_to_input(self.traveller_birthday, day)

    def set_buyer_data(self, buyer):
        self.set_buyer_first_name(buyer.first_name)
        self.set_buyer_second_name(buyer.middle_name)
        self.set_buyer_last_name(buyer.last_name)
        self.set_buyer_birthday(buyer.birthday)
        self.set_buyer_email(buyer.email)
        self.set_buyer_phone(buyer.phone)

    @page_element_operation
    def set_buyer_first_name(self, name):
        if self.buyer_first_name:
            language_chars = self.buyer_first_name.get_attribute("data-validation").lower()
            if language_chars == "latin":
                self.type_data_to_input(self.buyer_first_name, name)
            if language_chars == "rus":
                self.app.policy_data.buyer_first_name = name = u'Тест'
                logger.warning("Russian characters expected in buyer first name, name changed to '%s'" % name)
                self.type_data_to_input(self.buyer_first_name, name)
            logger.success("Buyer first name set to '{0}'".format(name))

    @page_element_operation
    def set_buyer_second_name(self, name):
        value_to_set = name if name else "-"
        if self.buyer_second_name:
            language_chars = self.buyer_second_name.get_attribute("data-validation").lower()
            if language_chars == "latin":
                self.type_data_to_input(self.buyer_second_name, value_to_set)
            if language_chars == "rus":
                logger.warning("Russian characters expected in buyer second name, name changed to 'Тест'")
                self.app.policy_data.buyer_second_name = name = u'Тест'
                self.type_data_to_input(self.buyer_second_name, name)
            logger.success("Buyer second name set to '{0}'".format(name))

    @page_element_operation
    def set_buyer_last_name(self, name):
        if self.buyer_last_name:
            language_chars = self.buyer_last_name.get_attribute("data-validation").lower()
            if language_chars == "latin":
                self.type_data_to_input(self.buyer_last_name, name)
            if language_chars == "rus":
                logger.warning("Russian characters expected in buyer last name, name changed to 'Тест'")
                self.app.policy_data.buyer_last_name = name = u'Тест'
                self.type_data_to_input(self.buyer_last_name, name)
            logger.success("Buyer last name set to '{0}'".format(name))

    @page_element_operation
    def set_buyer_birthday(self, day=None):
        if self.buyer_birthday:
            self.type_data_to_input(self.buyer_birthday, day)
            logger.success("Buyer birthday set to '{0}'".format(day))

    @page_element_operation
    def set_buyer_email(self, email):
        if self.buyer_email:
            self.type_data_to_input(self.buyer_email, email)
            logger.success("Buyer email set to '{0}'".format(email))

    @page_element_operation
    def set_buyer_phone(self, phone):
        if self.buyer_phone:
            self.type_data_to_input(self.buyer_phone, phone)
            logger.success("Buyer phone set to '{0}'".format(phone))

    @page_element_operation
    def compare_price_expected_and_actual(self, expected_price_rub):
        displayed_price = self.price_from_page
        if displayed_price == expected_price_rub:
            logger.success("Policy price displayed (%.2f) matches expected (%.2f)" % (displayed_price, expected_price_rub))
        else:
            self.result = False
            logger.fail("Policy price displayed (%.2f) matches expected (%.2f)" % (displayed_price, expected_price_rub))

    @page_element_operation
    def continue_operation_to_payment(self):
        self.submit_button.click()
        self.make_screenshot_if_needed(suffix=self.screenshot_name_suffix + "_ready")
        return self.get_page_result()
