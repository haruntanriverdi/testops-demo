import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from pages.base_page import BasePage


class OpenPositionsPage(BasePage):
    FILTER_LOCATION = (By.ID, "filter-by-location")
    FILTER_DEPT = (By.ID, "filter-by-department")

    JOB_ITEM = (By.CSS_SELECTOR, ".position-list-item-wrapper")
    JOB_TITLE = (By.CSS_SELECTOR, ".position-title")
    JOB_DEPT = (By.CSS_SELECTOR, ".position-department")
    JOB_LOC = (By.CSS_SELECTOR, ".position-location")
    BTN_VIEW = (By.CSS_SELECTOR, "a[href*='lever.co']")

    def wait_ready(self):
        self.wait_page_load()
        self.accept_cookies()
        self.find_visible(self.FILTER_LOCATION, timeout=30)

    def select_location(self, loc):
        el = self.find_clickable(self.FILTER_LOCATION)
        self.scroll_to(el)
        Select(el).select_by_visible_text(loc)
        self._wait_jobs_load()

    def select_department(self, dept):
        el = self.find_clickable(self.FILTER_DEPT)
        self.scroll_to(el)
        Select(el).select_by_visible_text(dept)
        self._wait_jobs_load()

    def _wait_jobs_load(self):
        time.sleep(1)
        cnt = len(self.driver.find_elements(*self.JOB_ITEM))
        for _ in range(5):
            time.sleep(0.5)
            new_cnt = len(self.driver.find_elements(*self.JOB_ITEM))
            if new_cnt == cnt:
                break
            cnt = new_cnt

    def get_jobs(self):
        try:
            self.find_visible(self.JOB_ITEM, timeout=10)
        except TimeoutException:
            return []
        items = self.driver.find_elements(*self.JOB_ITEM)
        return [i for i in items if i.is_displayed()]

    def get_job_info(self, el):
        return {
            "position": el.find_element(*self.JOB_TITLE).text,
            "department": el.find_element(*self.JOB_DEPT).text,
            "location": el.find_element(*self.JOB_LOC).text
        }

    def click_view_role(self, job_el):
        self.scroll_to(job_el)
        self.hover(job_el)
        job_el.find_element(*self.BTN_VIEW).click()
