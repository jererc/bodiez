from playwright.sync_api import TimeoutError

from bodiez.parsers.base import BaseParser


class GenericParser(BaseParser):
    id = 'generic'

    @staticmethod
    def can_parse(url_item):
        try:
            return bool(url_item.params['main_xpath'])
        except KeyError:
            return False

    def _request_handler(self, route, request):
        if request.resource_type == 'image':
            route.abort()
        else:
            route.continue_()

    def parse(self, url_item):
        with self.playwright_context() as context:
            context.route('**/*', self._request_handler)
            page = context.new_page()
            page.goto(url_item.url)
            selector = f'xpath={url_item.params["main_xpath"]}'
            try:
                page.wait_for_selector(selector, timeout=10000)
            except TimeoutError:
                return
            for element in page.locator(selector).element_handles():
                text_elements = [element.query_selector(f'xpath={x}')
                    for x in url_item.params['text_xpaths']]
                yield ', '.join([r.text_content().strip() if r else 'NULL'
                    for r in text_elements])
