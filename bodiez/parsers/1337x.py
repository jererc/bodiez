from urllib.parse import urlparse

from playwright.sync_api import TimeoutError

from bodiez.parsers.base import BaseParser


class X1337xParser(BaseParser):
    id = '1337x'

    @staticmethod
    def can_parse_url(url):
        return '1337x' in urlparse(url).netloc.split('.')

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
            selector = 'xpath=//table/tbody/tr'
            try:
                page.wait_for_selector(selector, timeout=10000)
            except TimeoutError:
                return
            for element in page.locator(selector).element_handles():
                title = element.query_selector_all('xpath=.//td')[0]
                yield title.text_content().strip()
