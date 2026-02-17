from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from pages.base_page import BasePage


class LeverPage(BasePage):
    BTN_APPLY = (By.CSS_SELECTOR, "a.postings-btn")

    def is_lever_page(self):
        return "jobs.lever.co" in self.driver.current_url

    def has_apply_btn(self):
        try:
            self.find_visible(self.BTN_APPLY, timeout=5)
            return True
        except TimeoutException:
            return False
