from urllib.parse import urlparse

from bodiez.parsers.base import BaseParser


class LexpresspropertyParser(BaseParser):
    id = 'lexpressproperty'

    @staticmethod
    def can_parse_url(url):
        res = urlparse(url)
        return 'lexpressproperty' in res.netloc.split('.')

    def _request_handler(self, route, request):
        if request.resource_type == 'image':
            route.abort()
        else:
            route.continue_()

    def parse(self, url):
        with self.playwright_context() as context:
            context.route('**/*', self._request_handler)
            page = context.new_page()
            page.goto(url)
            selector = 'xpath=//div[contains(@class, "card-row")]'
            page.wait_for_selector(selector, timeout=10000)
            for element in page.locator(selector).element_handles():
                title = element.query_selector('xpath=.//div[contains(@class, '
                    '"title-holder")]/h2')
                address = element.query_selector('xpath=.//address')
                price = element.query_selector('xpath=.//div[contains(@class, '
                    '"card-foot-price")]/strong/a')
                yield ', '.join([r.text_content().strip()
                    for r in (title, address, price)])
