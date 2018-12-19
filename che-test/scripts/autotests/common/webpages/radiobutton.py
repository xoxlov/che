# -*- coding: utf-8; -*-
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from common.webpages.base_element import BaseElement


class RadioButton(BaseElement):
    def __init__(self, webdriver, name, locator, description):
        super().__init__(webdriver, name, locator, description)
        self.type = "radio button"
        self.value = None

    def get_element_by_value(self, value):
        self.value = value
        assert self.value, "{} given value={} is wrong ({})".format(
            self.name, value, self.description)
        return self.get_element()

    def get_element(self):
        try:
            self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, self.locator)))
            return self.driver.find_element_by_css_selector(
                "{}[value='{}']".format(self.locator, self.value))
        except TimeoutException:
            message = "Cannot find {} {} ({})".format(self.name, self.type, self.description)
            raise TimeoutException(message)

    def is_selected(self, value):
        return self.get_element_by_value(value).is_selected()

    def set(self, value):
        if not self.value:
            return
        self.value = value
        self.wait_until_clickable()
        if not self.get_element_by_value(self.value).is_selected():
            self.get_element_by_value(value).click()

    def restore(self):
        self.set(self.value)
