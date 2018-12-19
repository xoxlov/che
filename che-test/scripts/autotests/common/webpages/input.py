# -*- coding: utf-8; -*-
from common.webpages.base_element import BaseElement
from selenium.webdriver.common.keys import Keys


class Input(BaseElement):
    def __init__(self, webdriver, name, locator, description):
        super().__init__(webdriver, name, locator, description)
        self.type = "input"

    def send_keys(self, keys):
        self.wait_until_clickable()
        self.click()
        self.get_element().clear()
        self.get_element().send_keys(keys)

    def send_more_keys(self, keys):
        self.wait_until_clickable()
        self.click()
        self.get_element().send_keys(keys)

    def set_value(self, value):
        self.send_keys(str(value))
        self.send_more_keys(Keys.TAB)

    def get_value(self):
        return self.get_element().get_property("value")
