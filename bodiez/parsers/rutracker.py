import time
from urllib.parse import urlparse

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from bodiez import logger
from bodiez.parsers.base import BaseParser


class RutrackerParser(BaseParser):
    id = 'rutracker'

    @staticmethod
    def can_parse_url(url):
        return 'rutracker' in urlparse(url).netloc.split('.')

    def _requires_login(self):
        try:
            return bool(self.driver.find_element(By.XPATH,
                '//input[@type="submit" and @name="login"]'))
        except NoSuchElementException:
            return False

    def _wait_for_elements(self, url, poll_frequency=.5, timeout=10):
        self.driver.get(url)
        end_ts = time.time() + timeout
        wait_for_login = False
        while time.time() < end_ts:
            try:
                els = self.driver.find_elements(By.XPATH,
                    '//div[contains(@class, "t-title")]')
                if not els:
                    raise NoSuchElementException()
                return els
            except NoSuchElementException:
                if self._requires_login() and not wait_for_login:
                    if self.headless:
                        raise Exception('requires login')
                    logger.info('waiting for user login...')
                    wait_for_login = True
                    end_ts += 120
                time.sleep(poll_frequency)
        raise Exception('timeout')

    def parse(self, url):
        for el in self._wait_for_elements(url):
            title_el = el.find_element(By.XPATH, './/a')
            title = title_el.text.strip()
            if not title:
                logger.error(f'failed to get {self.id} title from:\n'
                    f'{title_el.get_attribute("outerHTML")}')
                continue
            yield title
