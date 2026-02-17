import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException


class BasePage:
    TIMEOUT = 15

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, self.TIMEOUT)

    def find(self, locator):
        return self.wait.until(EC.presence_of_element_located(locator))

    def find_visible(self, locator, timeout=None):
        t = timeout if timeout else self.TIMEOUT
        return WebDriverWait(self.driver, t).until(EC.visibility_of_element_located(locator))

    def find_clickable(self, locator):
        return self.wait.until(EC.element_to_be_clickable(locator))

    def find_all(self, locator):
        return self.wait.until(EC.presence_of_all_elements_located(locator))

    def click(self, locator):
        self.find_clickable(locator).click()

    def scroll_to(self, el):
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.3)

    def hover(self, el):
        ActionChains(self.driver).move_to_element(el).perform()

    def current_url(self):
        return self.driver.current_url

    def switch_to_new_tab(self):
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def wait_page_load(self):
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    def accept_cookies(self):
        selectors = [
            (By.ID, "wt-cli-accept-all-btn"),
            (By.CSS_SELECTOR, "[data-cli_action='accept_all']"),
            (By.XPATH, "//a[contains(text(),'Accept All')]"),
            (By.CSS_SELECTOR, "button.accept-cookies")
        ]
        for sel in selectors:
            try:
                WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable(sel)).click()
                time.sleep(0.3)
                break
            except TimeoutException:
                pass
