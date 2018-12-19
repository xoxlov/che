# -*- coding: utf-8; -*-
from selenium.webdriver.common.by import By

from common.webpages.pageobject import PageObject
from common.webpages.pageobject import page_element_operation
from common.config_module import get_value_from_config
from model.car_number import CarNumber

from common.config_module import get_dir_by_suffix


class OsagoTitlePage(PageObject):

    def __init__(self, app):
        super().__init__(app)
        self.main_page_timeout = int(
            get_value_from_config("['osago_pages']['main_page_timeout']", self.config_file_name))
        self.page_name = "Cherehapa OSAGO main page"
        self.screenshot_name_suffix = "osago_main_page"
        self.expected_titles = ["Cherehapa"]

    @property
    def button_active_insurance(self):
        return self.driver.find_element_by_css_selector(".switched-on")

    @property
    def button_inactive_insurance(self):
        return self.driver.find_element_by_css_selector(".switched-off")

    @property
    def button_auto_insurance(self):
        return self.driver.find_element_by_css_selector(".page-auto")

    @property
    def button_travel_insurance(self):
        return self.driver.find_element_by_css_selector(".page-travel")

    @property
    def car_registration_number(self):
        return self.driver.find_element_by_css_selector("input[name='registrationNumber']")

    @property
    def car_region(self):
        return self.driver.find_element_by_css_selector("input[name='region']")

    @property
    def button_find_insurance(self):
        return self.driver.find_element_by_css_selector(".osago .submit-button")

    def open(self):
        if self.driver.current_url != self.app.target_url:
            self.driver.get(self.app.target_url)
        return self.is_travel_page_open()

    def open_osago_page(self):
        self.open()
        if not self.driver.find_elements_by_xpath("//*[contains(text(), 'ОСАГО')]"):
            self.button_auto_insurance.click()
        return self.is_osago_page_open()

    def is_travel_page_open(self):
        return self.wait_for_page_to_be_loaded(self.main_page_timeout, By.CLASS_NAME, "page-travel")

    def is_osago_page_open(self):
        return self.wait_for_page_to_be_loaded(self.main_page_timeout, By.CLASS_NAME, "osago")

    def is_auto_insurance_active(self):
        return self.button_active_insurance == self.button_auto_insurance

    def is_auto_insurance_inactive(self):
        return self.button_inactive_insurance == self.button_auto_insurance

    def is_travel_insurance_active(self):
        return self.button_active_insurance == self.button_travel_insurance

    def is_travel_insurance_inactive(self):
        return self.button_inactive_insurance == self.button_travel_insurance

    def is_car_number_empty(self):
        return self.car_registration_number.get_property("value") == ""

    def is_car_region_empty(self):
        return self.car_region.get_property("value") == ""

    def input_car_number_and_region(self, car_number):
        self.type_data_to_input(self.car_registration_number, car_number.number)
        self.type_data_to_input(self.car_region, car_number.region)

    def read_car_number_and_region(self):
        return CarNumber(number=self.car_registration_number.get_property("value"),
                         region=self.car_region.get_property("value"))

    def is_car_number_error_hidden(self):
        # FIXME: need implementation
        return True

    def is_car_number_error_displayed(self):
        # FIXME: need implementation
        return False

    @page_element_operation
    def start_insurance_search(self):
        self.make_screenshot_if_needed("osago_ready_to_find_insurance")
        self.button_find_insurance.click()
        # FIXME: явный переход на вторую страницу не требуется, всё должно происходить по нажатию кнопки
        self.driver.get("file://" + get_dir_by_suffix("che-test/scripts/autotests/html/osago_2.html"))
        return True
