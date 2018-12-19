# -*- coding: utf-8; -*-
from selenium.webdriver.common.by import By
from common.webpages.pageobject import PageObject
from common.config_module import get_value_from_config


class OsagoPolicyDetailsPage(PageObject):

    def __init__(self, app):
        super().__init__(app)
        self.main_page_timeout = \
            int(get_value_from_config("['osago_pages']['main_page_timeout']",
                                      self.config_file_name))
        self.page_name = "Cherehapa OSAGO Third page"
        self.screenshot_name_suffix = "osago_third_page"
        self.expected_titles = ["FIXME"]

    def wait(self):
        self.result = True
        return self.wait_for_page_to_be_loaded(
            self.main_page_timeout, By.NAME, "FIXME")
