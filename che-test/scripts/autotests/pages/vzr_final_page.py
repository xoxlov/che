# -*- coding: utf-8; -*-
import time
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait

from common.webpages.pageobject import PageObject
import common.logger as logger
from common.config_module import get_value_from_config


class FinalPage(PageObject):

    def __init__(self, app):
        super(FinalPage, self).__init__(app)
        self.page_name = "Policy Final page"
        self.screenshot_name_suffix = "final_page"
        self.policy_readyness_timeout = int(get_value_from_config("['vzr_pages']['policy_readyness_timeout']", self.config_file_name))
        self.wait = WebDriverWait(self.driver, self.policy_readyness_timeout)
        self.expected_titles = ["Готово!"]

    @property
    def section_complete(self):
        found = self.driver.find_elements_by_css_selector(".complete")
        return found[0] if found else None

    @property
    def error_message_exclamation(self):
        found = self.driver.find_elements_by_css_selector(".fa-exclamation-triangle")
        return found[0] if found and found[0].is_displayed() else None

    @property
    def error_message_text(self):
        found = self.driver.find_elements_by_css_selector(".error-text")
        return found[0].text if found else ""

    @property
    def button_close_error_message_modal(self):
        found = self.driver.find_elements_by_css_selector("div#errorModal button.close")
        return found[0] if found else None

    @property
    def policy_complete_link(self):
        found = self.driver.find_elements_by_css_selector(".complete_link")
        return found[0] if found else None

    @property
    def policy_wait_text(self):
        found = self.driver.find_elements_by_css_selector(".wait-text")
        return found[0] if found else None

    def is_error_message_detected(self):
        pass

    def wait_for_final_page(self):
        try:
            self.result = True
            logger.start(self.page_name)
            self.wait_until_complete_or_error()
            if self.error_message_exclamation:
                self.process_error_while_creating_policy()
            elif self.policy_wait_text:  # policy is still under processing
                self.process_success_while_creating_policy()
            else:
                self.process_success_after_creating_policy()
        except TimeoutException:
            self.process_policy_was_not_completed()
        finally:
            return self.get_page_result()

    def wait_until_complete_or_error(self):
        end_time = time.time() + self.policy_readyness_timeout
        while True:
            if self.section_complete or self.error_message_exclamation:
                return True
            time.sleep(self.loop_time_delta)
            if time.time() > end_time:
                raise TimeoutException("Cannot find either poliсy completeness element or failure element (error exclamation)")

    def process_error_while_creating_policy(self):
        self.result = False
        self.make_screenshot("error_while_creating_policy")
        error_text = ": %s" % self.error_message_text if self.error_message_text else ""
        logger.error("Error detected when creating policy%s" % error_text)
        self.report_error_with_screenshot()
        self.button_close_error_message_modal.click()
        self.app.policy_data.use_tempmail = False
        logger.fail("Policy created successfully")
        self.app.policy_data.task_id = None
        logger.warning("Database and email checks will be skipped")
        self.make_screenshot(suffix=self.screenshot_name_suffix + "_fail")

    def process_success_while_creating_policy(self):
        # policy is still under processing, but it can be completed pretty fast
        # also (because of bug) the page still receive status update in percents, that can be displayed
        logger.success("Policy creation in progress")
        self.app.policy_data.check_parent_task_only = True
        logger.warning("Only parent task will be checked in Database, other Database and email checks will be skipped")
        self.expected_titles = [u"% готовность полиса".encode("utf-8"), u"Подготовка страхового полиса".encode("utf-8"), u"Готово!".encode("utf-8")]
        self.result = self.verify_page_title(verbose=True)

    def process_success_after_creating_policy(self):
        self.result = self.verify_page_title(verbose=True)
        logger.success("Policy created successfully")

    def process_policy_was_not_completed(self):
        logger.warning("Policy creation was not completed!")
        self.app.policy_data.use_tempmail = False
        self.make_screenshot(suffix=self.screenshot_name_suffix + "_incomplete")
        if self.section_complete is None:
            logger.success("Policy creation process was completed, but the policy is still under processing")
            logger.warning("No policy id available at the moment, checks of final page and mail will be skipped")
            self.app.policy_data.task_id = None
