from playwright.sync_api import TimeoutError

from bodiez.parsers.base import BaseParser


class ChildElementParser(BaseParser):
    id = 'child_element'

    def can_parse(self):
        try:
            return (bool(self.url_item.parent_xpath)
                and bool(self.url_item.child_xpaths))
        except KeyError:
            return False

    def parse(self):
        with self.playwright_context() as context:
            page = context.new_page()
            page.goto(self.url_item.url)
            selector = f'xpath={self.url_item.parent_xpath}'
            try:
                page.wait_for_selector(selector, timeout=self.timeout)
            except TimeoutError:
                return
            for element in page.locator(selector).element_handles():
                children = [element.query_selector(f'xpath={x}')
                    for x in self.url_item.child_xpaths]
                yield ', '.join([r.text_content().strip() if r else 'NULL'
                    for r in children])
