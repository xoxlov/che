# -*- coding: utf-8; -*-
import functools
import datetime
import time
import os.path
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

import common.logger as logger
import common.webpages.expected_conditions_extended as EC_ext
from common.config_module import get_value_from_config, get_dir_by_suffix


def page_element_operation(method_to_decorate):
    @functools.wraps(method_to_decorate)
    def page_wrapper(self, *kargs):
        try:
            return method_to_decorate(self, *kargs)
        except Exception:
            logger.error("Cannot execute '{method}{args}'"
                         "".format(method=method_to_decorate.__name__, args=kargs))
            raise
    return page_wrapper


class PageError(Exception):
    pass


class PageObject(object):
    def __init__(self, app):
        self.app = app
        self.driver = app.webdriver

        self.page_name = ""
        self.result = True
        self.expected_titles = None

        self.config_file_name = get_dir_by_suffix("che-test/scripts/autotests/config/pageobjects.json")
        env_path = get_dir_by_suffix("che-test/scripts/autotests/config/env.json")
        self.make_screenshots = \
            get_value_from_config("['environment']['make_screenshots']", env_path)
        self.screenshot_name_suffix = \
            get_value_from_config("['path']['screenshot_name_suffix']", self.config_file_name)
        screenshot_catalog_name = \
            get_value_from_config("['path']['screenshot_catalog']", self.config_file_name)
        self.screenshot_catalog = get_dir_by_suffix("che-test/scripts/autotests/" + screenshot_catalog_name)
        self.prepare_screenshots_catalog()

        self.max_wait_for_title = \
            float(get_value_from_config("['timeouts']['max_wait_for_title']", self.config_file_name))
        self.loop_time_delta = \
            float(get_value_from_config("['timeouts']['loop_time_delta']", self.config_file_name))
        self.element_wait_timeout = \
            float(get_value_from_config("['timeouts']['element_wait_time_delta']", self.config_file_name))
        self.max_wait_for_login = \
            float(get_value_from_config("['timeouts']['max_wait_for_login']", self.config_file_name))

    def prepare_screenshots_catalog(self):
        if not os.path.exists(self.screenshot_catalog):
            os.mkdir(self.screenshot_catalog)

    def wait_for_page_to_be_loaded(self, timeout, by, locator):
        try:
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, locator)))
            return True
        except TimeoutException:
            logger.fail("{page} is loaded".format(page=self.page_name))
            self.result = False
            raise PageError("ERROR: {page} cannot be loaded within expected timeout".format(page=self.page_name))

    def verify_page_title(self, verbose=False):
        if self.expected_titles is None:
            return True
        # wait for title of the page to become valid
        start_check = datetime.datetime.now()
        while datetime.datetime.now() < start_check + datetime.timedelta(seconds=self.max_wait_for_title):
            actual_title = self.driver.title
            # if any([title in actual_title for title in self.expected_titles]):
            for title in self.expected_titles:
                if title in actual_title:
                    if verbose:
                        logger.success("Validate web page title '{title}'"
                                       "".format(title=self.driver.title))
                    return True
        # page title was not validated, print debug info and raise exception
        logger.fail("Validate web page title within {time} seconds".format(time=self.max_wait_for_title))
        string_from_unicode_list = "".join(["['", "', '".join(self.expected_titles), "']"])
        logger.debug("Expected titles: {titles}".format(titles=string_from_unicode_list))
        logger.debug("Actual title: '{title}'".format(title=self.driver.title))
        self.report_error_with_screenshot()
        return False

    def report_error_with_screenshot(self):
        self.make_screenshot("browser-at-test-failure-moment")

    def make_screenshot_if_needed(self, suffix=None):
        if self.make_screenshots:
            self.make_screenshot(suffix)

    def make_screenshot(self, suffix=None):
        suffix = suffix or self.screenshot_name_suffix
        str_time_now = datetime.datetime.strftime(datetime.datetime.now(), "sshot_%Y_%m_%d_%H_%M_%S_")
        screenshot_name = os.path.abspath(os.path.join(self.screenshot_catalog, str_time_now + suffix + ".png"))
        self.driver.save_screenshot(screenshot_name)

    @staticmethod
    def type_data_to_input(locator, value):
        assert locator, "Cannot find on page element '%s'" % locator
        locator.clear()
        # browser controls compatibility requires data to be filled by single chars
        for char in value:
            locator.send_keys(char)
        locator.send_keys(Keys.TAB)
        return locator.get_property("value") == value

    @staticmethod
    def send_keys(locator, value):
        # browser controls compatibility requires data to be filled by single chars
        assert locator, "Cannot find on page element '%s'" % locator
        locator.clear()
        for char in value:
            locator.send_keys(char)
        return locator.get_property("value") == value

    def get_page_result(self):
        logger.finishSuccess(self.page_name) if self.result else logger.finishFail(self.page_name)
        logger.print_empty_line()
        return self.result

    def search_element_is_only_one(self, by, locator, max_time=1.0):
        start_time = time.time()
        while True:
            dropdown_items = self.driver.find_elements(by, locator)
            if len(dropdown_items) == 1:
                return True
            if time.time() - start_time > max_time:
                return False
            time.sleep(self.loop_time_delta)

    def wait_for_element_clickable_by_locator(self, locator):
        try:
            WebDriverWait(self.driver, self.element_wait_timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, locator)))
            WebDriverWait(self.driver, self.element_wait_timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, locator)))
            return True
        except TimeoutException:
            return False

    def wait_notification_to_disappear(self):
        # Notification was detected, waiting for it to disappear..
        WebDriverWait(self.driver, self.max_wait_for_title).until_not(
            EC.presence_of_element_located((By.CLASS_NAME, "ui-pnotify")))

    def is_login_modal_form_ready(self):
        WebDriverWait(self.driver, self.element_wait_timeout).until(EC.element_to_be_clickable((By.ID, "modal_login")))
        return self.driver.find_element_by_css_selector("#modal_login")

    @property
    def login_modal_form_username(self):
        return self.driver.find_element_by_css_selector("#modal_login [name='login']")

    @property
    def login_modal_form_password(self):
        return self.driver.find_element_by_css_selector("#modal_login [name='password']")

    @property
    def login_modal_form_submit_button(self):
        return self.driver.find_element_by_css_selector("#modal_login button[type='submit']")

    def login_to_personal_cabinet(self, page_specific_css_locator=None):
        self.wait_notification_to_disappear()
        config_name = "config/personal_cabinet.json"
        username = get_value_from_config("['adm_user']", config_name)
        password = get_value_from_config("['adm_user_password']", config_name)
        WebDriverWait(self.driver, self.max_wait_for_login).until(
            EC.element_to_be_clickable((By.ID, "loginModalLink")))
        self.driver.find_element_by_css_selector("#loginModalLink").click()

        self.is_login_modal_form_ready()
        self.type_data_to_input(self.login_modal_form_username, username)
        self.type_data_to_input(self.login_modal_form_password, password)
        self.login_modal_form_submit_button.click()

        self.wait_and_check_if_user_is_logged()
        WebDriverWait(self.driver, self.max_wait_for_login).until_not(
            EC.element_to_be_clickable((By.ID, "loginModalLabel")))
        if page_specific_css_locator:
            WebDriverWait(self.driver, self.max_wait_for_login).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, page_specific_css_locator)))
        logger.success("Logged successfully as 'user'".format(user=username))

    def wait_and_check_if_user_is_logged(self):
        WebDriverWait(self.driver, self.max_wait_for_login).until(
                EC_ext.visibility_of_any_elements_from_list_located(
                    [(By.CSS_SELECTOR, ".top-lk"), (By.CSS_SELECTOR, ".lk>ul")]
                )
        )
        return True
