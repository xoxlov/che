# -*- coding: utf-8; -*-
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import WebDriverException

from common.system import execute_which_in_shell


class Browser:
    def __init__(self):
        self.browser_name = None
        self.browser_path = None

    def __del__(self):
        pass

    def run(self, name="firefox"):
        if name in ["google-chrome", "chrome"]:
            self.browser_name = "google-chrome"
            return self.get_chrome()
        if name in ["firefox"]:
            self.browser_name = "firefox"
            return self.get_firefox()
        raise WebDriverException("Browser is not set, cannot continue")

    def check_browser_is_available(self):
        # check we have browser in $PATH
        self.browser_path = execute_which_in_shell(self.browser_name)

    def get_chrome(self):
        self.check_browser_is_available()
        capabilities = DesiredCapabilities.CHROME
        capabilities['binary'] = self.browser_path
        capabilities['browserName'] = self.browser_name
        service_log_path = "{}/chromedriver.log".format(".")
        service_args = ['--verbose']
        browser = webdriver.Chrome(service_args=service_args,
                                   service_log_path=service_log_path)
        return browser

    def get_firefox(self):
        self.check_browser_is_available()
        capabilities = DesiredCapabilities.FIREFOX
        capabilities['marionette'] = True
        profile = webdriver.FirefoxProfile()
        profile.set_preference('webdriver.log.file', './firefox_console.log')
        profile.update_preferences()
        return webdriver.Firefox(capabilities=capabilities,
                                 firefox_profile=profile, log_path="/dev/null")
