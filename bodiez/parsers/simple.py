from playwright.sync_api import TimeoutError

from bodiez.parsers.base import BaseParser


class SimpleParser(BaseParser):
    id = 'simple'

    def can_parse(self):
        try:
            return bool(self.url_item.xpath)
        except KeyError:
            return False

    def parse(self):
        with self.playwright_context() as context:
            page = context.new_page()
            page.goto(self.url_item.url)
            selector = f'xpath={self.url_item.xpath}'
            try:
                page.wait_for_selector(selector, timeout=self.timeout)
            except TimeoutError:
                return
            for element in page.locator(selector).all():
                yield element.text_content().strip()
