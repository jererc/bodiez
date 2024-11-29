from urllib.parse import urlparse

from playwright.sync_api import TimeoutError

from bodiez.parsers.base import BaseParser


class RutrackerParser(BaseParser):
    id = 'rutracker'

    @staticmethod
    def can_parse_url(url):
        return 'rutracker' in urlparse(url).netloc.split('.')

    def _request_handler(self, route, request):
        if request.resource_type == 'image' or '1xbet' in request.url:
            route.abort()
        else:
            route.continue_()

    def parse(self, url):
        with self.playwright_context() as context:
            context.route('**/*', self._request_handler)
            page = context.new_page()
            page.goto(url)
            selector = 'xpath=//div[contains(@class, "t-title")]'
            timeout = 10000 if self.config.HEADLESS else 120000
            try:
                page.wait_for_selector(selector, timeout=timeout)
            except TimeoutError:
                raise Exception('requires interactive login')
            elements = page.locator(selector).element_handles()
            for element in elements:
                a = element.query_selector('xpath=.//a')
                yield a.text_content().strip()
