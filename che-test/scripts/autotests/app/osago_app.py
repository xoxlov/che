# -*- coding: utf-8; -*-
import common.config_module as config_module
from common.browser import Browser
from pages.osago_main_page import OsagoTitlePage
from pages.osago_calculator_page import OsagoCalculatorPage
from pages.osago_policy_details_page import OsagoPolicyDetailsPage
from common.config_module import get_dir_by_suffix, get_value_from_config


class CheWebOsagoApplication:

    def __init__(self, config=None):
        config_path = config_module.get_dir_by_suffix("che-test/scripts/autotests/config/env.json")
        self.config = config or config_module.load(config_path)
        self.partner_id = None

        # environment options
        self.make_target_url()
        self.make_screenshots = self.config["environment"]["make_screenshots"]
        self.webdriver = Browser().run(self.config["environment"]["browser"])

        self.target_url = None

        self.main_page = OsagoTitlePage(self)
        self.calculator_page = OsagoCalculatorPage(self)
        self.policy_details_page = OsagoPolicyDetailsPage(self)

    def __del__(self):
        if self.webdriver is None:
            return
        self.webdriver.quit()
        self.webdriver = None

    def __enter__(self):
        return self

    def __exit__(self, ttype, value, traceback):
        self.__del__()

    def destroy(self):
        self.__del__()

    def make_target_url(self):
        # FIXME: адрес страницы должен быть из конфига
        file_name = get_dir_by_suffix(get_value_from_config("['base_url']", "config/osago.json"))
        self.target_url = "file://" + file_name
        return self.target_url
