# -*- coding: utf-8; -*-
import time
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from common.webpages.pageobject import PageObject
import common.logger as logger
from common.config_module import get_value_from_config


class PolicyCreationAnimatedPage(PageObject):

    def __init__(self, app):
        super(PolicyCreationAnimatedPage, self).__init__(app)
        self.page_name = "Policy Creation Animated page"
        self.screenshot_name_suffix = "policy_creation_animated_page"
        self.policy_creation_animated_timeout = \
            float(get_value_from_config("['vzr_pages']['policy_creation_animated_timeout']", self.config_file_name))
        self.wait = WebDriverWait(self.driver, self.policy_creation_animated_timeout)

        self.expected_titles = ["% готовность полиса", "Заполнение платежных данных"]

    @property
    def task_id_from_page(self):
        try:
            taskid = self.driver.find_element_by_css_selector('.payment-info').get_property("dataset").get('taskid')
            return taskid if taskid else None
        except WebDriverException:
            return None

    def wait_for_policy_creation_page(self):
        logger.start(self.page_name)
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#polisCreatingModal")))
            self.result = self.verify_page_title(verbose=True)
        except TimeoutException:
            self.result = False

    def get_task_id(self):
        self.app.policy_data.task_id = None
        for sleeptime in range(0, int(self.policy_creation_animated_timeout)):
            time.sleep(self.loop_time_delta)
            self.app.policy_data.task_id = self.task_id_from_page
            if self.app.policy_data.task_id is not None:
                logger.success("Task ID for policy was successfully found, task_id = %s" % self.app.policy_data.task_id)
                break
        else:
            logger.fail("Task ID for policy was found on the page")
            self.result = False
            logger.warning("No parent task_id available, SQL check will be skipped")
        return self.get_page_result()
