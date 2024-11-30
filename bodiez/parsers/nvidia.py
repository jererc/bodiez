from urllib.parse import urlparse

from bodiez.parsers.base import BaseParser


class NvidiaGeforceParser(BaseParser):
    id = 'nvidia.geforce'

    @staticmethod
    def can_parse_url(url):
        res = urlparse(url)
        return 'nvidia' in res.netloc.split('.') \
            and res.path.strip('/').endswith('/geforce/news')

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
            selector = 'xpath=//div[contains(@class, "article-title-text")]'
            page.wait_for_selector(selector, timeout=10000)
            elements = page.locator(selector).element_handles()
            for element in elements:
                title = element.query_selector('xpath=.//a')
                yield title.text_content().strip()
