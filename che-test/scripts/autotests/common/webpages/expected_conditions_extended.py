# -*- coding: utf-8; -*-
from selenium.webdriver.support import expected_conditions as EC


class visibility_of_any_elements_from_list_located(object):
    """ An expectation for checking that there is at least one element from the given list visible on a web page.
    Locator is used to find the elements, should be a tuple or a list of tuples (By, locator_string).
    Returns the list of WebElements once they are located.
    """
    def __init__(self, locator):
        if isinstance(locator, tuple):
            locator = [locator]
        self.locator = locator

    def __call__(self, driver):
        # Note: list normalization is used
        # >>> l = [[1, 2, 3], [4, 5], [6], [7, 8, 9]]
        # >>> sum(l, [])
        # [1, 2, 3, 4, 5, 6, 7, 8, 9]
        return [element for element in sum([EC._find_elements(driver, locator) for locator in self.locator], [])
                if EC._element_if_visible(element)]
