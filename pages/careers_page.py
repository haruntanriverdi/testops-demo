from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from pages.base_page import BasePage


class CareersPage(BasePage):
    URL = "https://example.com/careers/quality-assurance/"

    BTN_SEE_ALL = (By.XPATH, "//a[contains(text(), 'See all QA jobs')]")
    BTN_SEE_ALL_ALT = (By.CSS_SELECTOR, "a[href*='qualityassurance']")

    def open(self):
        self.driver.get(self.URL)
        self.wait_page_load()
        self.accept_cookies()
        return self

    def is_loaded(self):
        self.wait_page_load()
        return "quality-assurance" in self.driver.current_url

    def click_see_all_jobs(self):
        try:
            btn = self.find_clickable(self.BTN_SEE_ALL)
        except TimeoutException:
            btn = self.find_clickable(self.BTN_SEE_ALL_ALT)
        self.scroll_to(btn)
        btn.click()
