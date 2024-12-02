from playwright.sync_api import TimeoutError

from bodiez.parsers.base import BaseParser


class SimpleParser(BaseParser):
    id = 'simple'

    @staticmethod
    def can_parse(url_item):
        try:
            return bool(url_item.params['xpath'])
        except KeyError:
            return False

    def parse(self, url_item):
        with self.playwright_context() as context:
            context.route('**/*', self._request_handler)
            page = context.new_page()
            page.goto(url_item.url)
            selector = f'xpath={url_item.params["xpath"]}'
            try:
                page.wait_for_selector(selector, timeout=self.timeout)
            except TimeoutError:
                return
            for element in page.locator(selector).all():
                yield element.text_content().strip()


class SubElementParser(BaseParser):
    id = 'sub_elements'

    @staticmethod
    def can_parse(url_item):
        try:
            return (bool(url_item.params['parent_xpath'])
                and bool(url_item.params['children_xpaths']))
        except KeyError:
            return False

    def parse(self, url_item):
        with self.playwright_context() as context:
            context.route('**/*', self._request_handler)
            page = context.new_page()
            page.goto(url_item.url)
            selector = f'xpath={url_item.params["parent_xpath"]}'
            try:
                page.wait_for_selector(selector, timeout=self.timeout)
            except TimeoutError:
                return
            for element in page.locator(selector).element_handles():
                children = [element.query_selector(f'xpath={x}')
                    for x in url_item.params['children_xpaths']]
                yield ', '.join([r.text_content().strip() if r else 'NULL'
                    for r in children])
