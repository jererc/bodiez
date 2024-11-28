from urllib.parse import urlparse

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

    def parse(self, url):
        with self.playwright_context() as context:
            context.route('**/*', self._request_handler)
            page = context.new_page()
            page.goto(url)
            trs = page.locator('xpath=//table/tbody/tr').all()
            for tr in trs:
                td = tr.locator('xpath=.//td').nth(0)
                yield td.text_content().strip()
