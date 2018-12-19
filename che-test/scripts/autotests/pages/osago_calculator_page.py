# -*- coding: utf-8; -*-
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from common.webpages.button import Button
from common.webpages.checkbox import CheckBox
from common.webpages.pageobject import PageObject
from common.config_module import get_value_from_config

from common.webpages.input import Input


class OsagoCalculatorPage(PageObject):

    def __init__(self, app):
        super().__init__(app)
        self.main_page_timeout = \
            int(get_value_from_config("['osago_pages']['main_page_timeout']",
                                      self.config_file_name))
        self.page_name = "Cherehapa OSAGO Second page"
        self.screenshot_name_suffix = "osago_second_page"
        self.expected_titles = ["OSAGO-2"]

        self.drivers_amount_limited_button = Button(
            webdriver=self.driver, name="1-5",
            locator=".FIXME",
            description="Количество водетелей 1-5")
        self.drivers_amount_unlimited_button = Button(
            webdriver=self.driver, name="unlimited",
            locator=".FIXME",
            description="Количество водетелей неограниченно")
        self.details_show_offer_0_button = Button(
            webdriver=self.driver, name="unlimited",
            locator=".FIXME",
            description="Кнопка 'подробнее' для первого предложения полисов")
        self.details_hide_offer_0_button = Button(
            webdriver=self.driver, name="unlimited",
            locator=".FIXME",
            description="Кнопка 'свернуть подробности' для первого предложения полисов")
        self.policy_buy_offer_0_button = Button(
            webdriver=self.driver, name="unlimited",
            locator=".FIXME",
            description="Кнопка 'Купить' для первого предложения полисов")

        self.no_vin_but_body_checkbox = CheckBox(
            webdriver=self.driver, name="no_vin_but_nody",
            locator=".FIXME",
            description="Флаг 'VIN отсутствует, есть номер кузова'")
        self.no_vin_but_chassis_checkbox = CheckBox(
            webdriver=self.driver, name="no_vin_but_chassis",
            locator=".FIXME",
            description="Флаг 'VIN отсутствует, есть номер шасси'")

        self.date_start_input = Input(
            webdriver=self.driver,
            name="policy.dateStart",
            locator="input[name='policy.dateStart']",
            description="Поле ввода даты начала поездки 'dateStart'")

    @property
    def use_purpose(self):
        found = self.app.webdriver.find_elements_by_css_selector("input[name='usePurpose']")
        return found[0] if found else None

    @property
    def offers_displayed(self):
        # FIXME: поставить корректный локатор
        return self.app.webdriver.find_elements_by_css_selector("div.offers")

    def get_price(self, locator):
        assert locator in self.offers_displayed
        # TODO
        return "--.--"

    def is_details_button_displayed(self, locator):
        assert locator in self.offers_displayed
        # TODO
        return False

    def is_details_block_hidden(self, locator):
        assert locator in self.offers_displayed
        # TODO
        return False

    def is_buy_button_enabled(self, locator):
        assert locator in self.offers_displayed
        # TODO
        return False

    def wait(self):
        self.result = True
        return self.wait_for_page_to_be_loaded(
            self.main_page_timeout, By.NAME, "isUnlimitedDrivers")

    def is_active(self):
        return self.app.webdriver.title in self.expected_titles

    def get_values_to_enter_count(self):
        # TODO
        return 0

    def get_auto_number(self):
        # TODO
        return None

    @property
    def change_number_button(self):
        # TODO
        return None

    @property
    def date_start_error_message(self):
        # TODO
        return None

    def is_date_start_checked_good(self):
        # TODO
        return False

    def set_date_start(self, value):
        self.date_start_input.send_keys(value + Keys.TAB)

    def get_insurable_period(self):
        # TODO
        return False

    def select_insurable_period(self, value):
        # TODO
        return

    def insurable_period_send_keys(self, keys):
        # TODO
        return

    def is_insurable_period_checked_good(self):
        # TODO
        return False

    def get_auto_category(self):
        # TODO
        return ""

    def select_auto_category(self, value):
        # TODO
        return

    def auto_category_send_keys(self, keys):
        # TODO
        return

    def is_auto_category_checked_good(self):
        # TODO
        return False

    @property
    def engine_power_error_message(self):
        return None

    def is_engine_power_checked_good(self):
        # TODO
        return False

    def get_engine_power(self):
        # TODO
        return ""

    def set_engine_power(self, value):
        # TODO
        return

    def engine_power_send_keys(self, keys):
        # TODO
        return

    def get_use_purpose_value(self):
        # TODO
        return ""

    def is_use_purpose_checked_good(self):
        # TODO
        return False

    def select_use_purpose(self, value):
        # TODO
        return

    def is_date_using_start_displayed(self):
        # TODO
        return True

    def get_date_using_start_value(self):
        # TODO
        return ""

    def is_date_using_start_checked_good(self):
        # TODO
        return False

    @property
    def date_using_start_error_message(self):
        return None

    def date_using_start_send_keys(self, keys):
        # TODO
        return
    
    def set_date_using_start(self, value):
        # TODO
        return

    def is_date_using_end_displayed(self):
        # TODO
        return True

    def get_date_using_end_value(self):
        # TODO
        return ""

    def is_date_using_end_checked_good(self):
        # TODO
        return False

    @property
    def date_using_end_error_message(self):
        return None

    def date_using_end_send_keys(self, keys):
        # TODO
        return

    def set_date_using_end(self, value):
        # TODO
        return

    def is_drivers_amount_limited(self):
        # TODO
        return False

    def is_drivers_amount_unlimited(self):
        # TODO
        return False

    def is_add_driver_button_displayed(self):
        # TODO
        return False

    def is_driver_1_icon_displayed(self):
        # TODO
        return False

    def is_driver_2_icon_displayed(self):
        # TODO
        return False

    def is_driver_3_icon_displayed(self):
        # TODO
        return False

    def is_driver_4_icon_displayed(self):
        # TODO
        return False

    def is_driver_5_icon_displayed(self):
        # TODO
        return False

    def is_driver_1_name_displayed(self):
        # TODO
        return False

    def get_driver_1_name_value(self):
        # TODO
        return ""

    def is_driver_1_checked_good(self):
        # TODO
        return False

    def set_driver_1_name(self, name):
        # TODO
        return False

    def is_driver_1_name_checked_good(self):
        # TODO
        return False

    @property
    def driver_1_name_error_message(self):
        # TODO
        return None

    def driver_1_name_send_keys(self, keys):
        # TODO
        return

    def is_driver_1_birthday_displayed(self):
        # TODO
        return False

    def get_driver_1_birthday(self):
        # TODO
        return ""

    def is_driver_1_birthday_checked_good(self):
        # TODO
        return False

    def set_driver_1_birthday_date(self):
        # TODO
        return False

    @property
    def date_driver_1_birthday_error_message(self):
        # TODO
        return None

    def date_driver_1_birthday_send_keys(self, keys):
        # TODO
        return

    def is_driver_1_first_license_date_displayed(self):
        # TODO
        return False

    def get_driver_1_first_license_date(self):
        # TODO
        return ""

    def is_driver_1_first_license_date_checked_good(self):
        # TODO
        return False

    def set_driver_1_first_license_date_date(self):
        # TODO
        return False

    @property
    def date_driver_1_first_license_date_error_message(self):
        # TODO
        return None

    def date_driver_1_first_license_date_send_keys(self, keys):
        # TODO
        return

    def is_driver_2_name_displayed(self):
        # TODO
        return False

    def get_driver_2_name_value(self):
        # TODO
        return ""

    def is_driver_2_checked_good(self):
        # TODO
        return False

    def set_driver_2_name(self, name):
        # TODO
        return False

    def is_driver_2_name_checked_good(self):
        # TODO
        return False

    @property
    def driver_2_name_error_message(self):
        # TODO
        return None

    def driver_2_name_send_keys(self, keys):
        # TODO
        return

    def is_driver_2_birthday_displayed(self):
        # TODO
        return False

    def get_driver_2_birthday(self):
        # TODO
        return ""

    def is_driver_2_birthday_checked_good(self):
        # TODO
        return False

    def set_driver_2_birthday_date(self):
        # TODO
        return False

    @property
    def date_driver_2_birthday_error_message(self):
        # TODO
        return None

    def date_driver_2_birthday_send_keys(self, keys):
        # TODO
        return

    def is_owner_birthday_displayed(self):
        # TODO
        return False

    def get_owner_birthday(self):
        # TODO
        return ""

    def is_owner_birthday_checked_good(self):
        # TODO
        return False

    def set_owner_birthday_date(self):
        # TODO
        return False

    @property
    def date_owner_birthday_error_message(self):
        # TODO
        return None

    def date_owner_birthday_send_keys(self, keys):
        # TODO
        return

    def is_owner_name_displayed(self):
        # TODO
        return False

    def get_owner_name_value(self):
        # TODO
        return ""

    def is_owner_checked_good(self):
        # TODO
        return False

    def set_owner_name(self, name):
        # TODO
        return False

    def is_owner_name_checked_good(self):
        # TODO
        return False

    @property
    def owner_name_error_message(self):
        # TODO
        return None

    def owner_name_send_keys(self, keys):
        # TODO
        return

    def is_driver_1_license_displayed(self):
        # TODO
        return False

    def get_driver_1_license(self):
        # TODO
        return None

    def is_driver_1_license_checked_good(self):
        # TODO
        return False

    def set_driver_1_license(self, value):
        # TODO
        return False

    @property
    def date_driver_1_license_error_message(self):
        # TODO
        return None

    def driver_1_license_send_keys(self, keys):
        # TODO
        return False

    def is_driver_2_license_displayed(self):
        # TODO
        return False

    def get_driver_2_license(self):
        # TODO
        return None

    def is_driver_2_license_checked_good(self):
        # TODO
        return False

    def set_driver_2_license(self, value):
        # TODO
        return False

    @property
    def date_driver_2_license_error_message(self):
        # TODO
        return None

    def driver_2_license_send_keys(self, keys):
        # TODO
        return False

    def is_owner_address_displayed(self):
        # TODO
        return False

    def get_owner_address(self):
        # TODO
        return None

    def is_owner_address_checked_good(self):
        # TODO
        return False

    def set_owner_address(self, value):
        # TODO
        return False

    @property
    def owner_address_error_message(self):
        # TODO
        return None

    def owner_address_send_keys(self, keys):
        # TODO
        return False

    def is_owner_passport_displayed(self):
        # TODO
        return False

    def get_owner_passport(self):
        # TODO
        return None

    def is_owner_passport_checked_good(self):
        # TODO
        return False

    def set_owner_passport(self, value):
        # TODO
        return False

    @property
    def owner_passport_error_message(self):
        # TODO
        return None

    def owner_passport_send_keys(self, keys):
        # TODO
        return False

    def is_vehicle_vin_input_displayed(self):
        # TODO
        return False

    def get_vehicle_vin(self):
        # TODO
        return None

    def is_vehicle_vin_checked_good(self):
        # TODO
        return False

    def set_vehicle_vin(self, value):
        # TODO
        return False

    @property
    def vehicle_vin_error_message(self):
        # TODO
        return None

    def vehicle_vin_input_send_keys(self, keys):
        # TODO
        return False

    def is_vehicle_vin_number_enabled(self):
        # TODO
        return False

    def is_vehicle_body_input_displayed(self):
        # TODO
        return False

    def get_vehicle_body_number(self):
        # TODO
        return None

    def is_vehicle_body_checked_good(self):
        # TODO
        return False

    def set_vehicle_body_number(self, value):
        # TODO
        return False

    @property
    def vehicle_body_error_message(self):
        # TODO
        return None

    def vehicle_body_input_send_keys(self, keys):
        # TODO
        return False

    def is_vehicle_chassis_input_displayed(self):
        # TODO
        return False

    def get_vehicle_chassis_number(self):
        # TODO
        return None

    def is_vehicle_chassis_checked_good(self):
        # TODO
        return False

    def set_vehicle_chassis_number(self, value):
        # TODO
        return False

    @property
    def vehicle_chassis_error_message(self):
        # TODO
        return None

    def vehicle_chassis_input_send_keys(self, keys):
        # TODO
        return False
