# -*- coding: utf-8; -*-
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from common.webpages.pageobject import PageObject
from common.webpages.pageobject import page_element_operation
import common.logger as logger
from common.config_module import get_value_from_config, load
from common.database import CheDb


class CherehapaMainPage(PageObject):

    def __init__(self, app):
        super(CherehapaMainPage, self).__init__(app)
        self.main_page_timeout = int(get_value_from_config("['vzr_pages']['main_page_timeout']", self.config_file_name))
        self.page_name = "Main Cherehapa page"
        self.screenshot_name_suffix = "main_page"
        self.expected_titles = [u'Cherehapa - Туристическая страховка онлайн'.encode("utf-8")]

    @property
    def add_country_link(self):
        return self.driver.find_element_by_css_selector("#add-new-country")

    @property
    def button_find_insurance(self):
        return self.driver.find_element_by_css_selector("button.btn-find-insurance")

    @property
    def country_to_travel(self):
        return self.driver.find_element_by_css_selector(".ms-sel-ctn input")

    @property
    def country_to_travel_dropdown_menu(self):
        found = self.driver.find_elements_by_css_selector(".ms-res-item-grouped")
        return found[0] if found else None

    @property
    def more_travellers(self):
        return self.driver.find_element_by_css_selector("#traveler_more")

    @property
    def policy_end_date(self):
        return self.driver.find_element_by_css_selector('#to')

    @property
    def policy_for_year(self):
        return self.driver.find_element_by_css_selector("#cb_multiple")

    @property
    def policy_start_date(self):
        return self.driver.find_element_by_css_selector('#from')

    @property
    def travel_already(self):
        return self.driver.find_element_by_css_selector("#cb_abroad")

    @property
    def traveller_age(self):
        return self.driver.find_elements_by_css_selector(".traveler_li .traveler_select")

    @property
    def traveller_input(self):
        return self.driver.find_element_by_css_selector("#traveler_input")

    @property
    def traveller_number(self):
        return self.driver.find_elements_by_css_selector(".traveler_li input")

    @property
    def yellow_line(self):
        return self.driver.find_element_by_css_selector("div.yellow-line")

    def open_main_cherehapa_page(self):
        self.result = True
        logger.start(self.page_name)
        self.driver.get(self.app.testing_url)
        self.wait_for_page_to_be_loaded(self.main_page_timeout, By.CLASS_NAME, "blue-footer")
        logger.success("{page} was loaded successfully".format(page=self.page_name))

    @page_element_operation
    def add_country_to_travel(self, country):
        self.add_country_link.click()
        self.set_country_to_travel(country)

    @page_element_operation
    def set_country_to_travel(self, *kargs):
        countries_list = kargs[0] if isinstance(kargs[0], list) else list(kargs)
        for country in countries_list:
            db = CheDb(load()["database"])
            country_name = db.get_country_by_code(country)
            del db
            self.country_to_travel.click()
            self.country_to_travel.send_keys(country_name)
            self.search_element_is_only_one(By.CSS_SELECTOR, ".ms-res-item-grouped")
            self.country_to_travel_dropdown_menu.click()
            logger.success("Added '%s' to the list of countries" % country_name)
        self.refresh_input_form()

    @page_element_operation
    def set_country_group_to_travel(self, *kargs):
        groups_list = kargs[0] if isinstance(kargs[0], list) else list(kargs)
        for group in groups_list:
            db = CheDb(load()["database"])
            group_name = db.get_country_group_by_code(group)
            del db
            self.country_to_travel.click()
            self.country_to_travel.send_keys(group_name)
            self.search_element_is_only_one(By.CSS_SELECTOR, ".ms-res-item-grouped")
            self.country_to_travel_dropdown_menu.click()
            logger.success("Added '%s' to the list of countries" % group_name)
        self.refresh_input_form()

    @page_element_operation
    def set_travel_start_date(self, date):
        self.policy_start_date.clear()
        self.policy_start_date.send_keys(date)
        self.refresh_input_form()
        logger.success("Start date for the policy is set to %s" % date)

    @page_element_operation
    def set_travel_end_date(self, date):
        self.policy_end_date.clear()
        self.policy_end_date.send_keys(date)
        self.refresh_input_form()
        logger.success("End date for the policy is set to %s" % date)

    @page_element_operation
    def set_travellers_age(self, *kargs):
        self.traveller_input.click()
        ages_list = kargs[0] if isinstance(kargs[0], list) else list(kargs)
        if len(ages_list) > 4:
            self.more_travellers.click()
        for count, age in enumerate(ages_list):
            self.traveller_number[count].click()
            Select(self.traveller_age[count]).select_by_value(str(age))
            logger.success("Age of traveller #{} is set to {}".format(count + 1, age))
        self.refresh_input_form()

    @page_element_operation
    def refresh_input_form(self):
        # optional action - click the empty space for input form to curl up
        self.yellow_line.click()

    @page_element_operation
    def start_insurance_search(self):
        self.make_screenshot_if_needed("values_ready_to_find_insurance")
        self.button_find_insurance.click()
        return self.get_page_result()
