# -*- coding: utf-8; -*-
from common.webpages.base_element import BaseElement


class Button(BaseElement):
    def __init__(self, webdriver, name, locator, description):
        super().__init__(webdriver, name, locator, description)
        self.type = "button"
