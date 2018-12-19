# -*- coding: utf-8; -*-
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


class BaseElement:
    def __init__(self, webdriver, name, locator, description):
        self.name = name
        self.driver = webdriver
        self.locator = locator
        self.description = description
        self.element_expect_timeout = 4
        self.wait = WebDriverWait(self.driver, self.element_expect_timeout)
        self.type = "element"

    def get_element(self):
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.locator)))
            return self.driver.find_element_by_css_selector(self.locator)
        except TimeoutException:
            message = "Cannot find {} {} ({})".format(self.name, self.type, self.description)
            raise TimeoutException(message)

    def is_displayed(self):
        return self.get_element().is_displayed()

    def is_enabled(self):
        return self.get_element().is_enabled()

    def wait_until_clickable(self):
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.locator)))
        try:
            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.locator)))
        except TimeoutException:
            message = "Element {} ({}) is not clickable".format(self.name, self.description)
            raise TimeoutException(message)

    def click(self):
        self.wait_until_clickable()
        self.get_element().click()
