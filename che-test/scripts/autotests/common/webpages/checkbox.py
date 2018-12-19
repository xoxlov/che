# -*- coding: utf-8; -*-
from common.webpages.base_element import BaseElement


class CheckBox(BaseElement):
    def __init__(self, webdriver, name, locator, description):
        super().__init__(webdriver, name, locator, description)
        self.type = "checkbox"
        self.value = None

    def is_selected(self):
        return self.get_element().is_selected()

    def set(self, state=True):
        if state is None:
            return
        self.value = bool(state)
        self.wait_until_clickable()
        if self.is_selected() != bool(self.value):
            self.click()

    def get_value(self):
        return bool(self.is_selected())

    def restore(self):
        self.set(self.value)
