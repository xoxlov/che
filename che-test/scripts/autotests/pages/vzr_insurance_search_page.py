# -*- coding: utf-8; -*-
from common.webpages.pageobject import PageObject
from selenium.webdriver.common.by import By

import common.logger as logger
from common.config_module import get_value_from_config


class InsuranceSearchPage(PageObject):

    def __init__(self, app):
        super(InsuranceSearchPage, self).__init__(app)
        self.insurance_search_timeout = int(get_value_from_config("['vzr_pages']['insurance_search_timeout']", self.config_file_name))
        self.page_name = "Insurance Search page"
        self.screenshot_name_suffix = "insurance_search_page"
        self.expected_titles = [u"Расчет стоимости страховки".encode("utf-8")]

    def wait_and_check_insurance_search_page(self):
        self.result = True
        logger.start(self.page_name)
        self.wait_for_page_to_be_loaded(self.insurance_search_timeout, By.CLASS_NAME, "progress-bar")
        logger.success("{page} was loaded successfully".format(page=self.page_name))
        return self.get_page_result()
