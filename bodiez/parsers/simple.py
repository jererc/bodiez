from bodiez.parsers.base import BaseParser


class SimpleElementParser(BaseParser):
    id = 'simple_element'

    def can_parse(self):
        return bool(self.url_item.xpath)

    def parse(self):
        with self.playwright_context() as context:
            page = context.new_page()
            page.goto(self.url_item.url)
            selector = f'xpath={self.url_item.xpath}'
            self._wait_for_selector(page, selector)
            for element in page.locator(selector).all():
                yield element.text_content().strip()
