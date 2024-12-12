from bodiez.parsers.base import BaseParser


class SimpleElementParser(BaseParser):
    id = 'simple_element'

    def can_parse(self):
        return bool(self.url_item.xpath)

    def _iterate_children(self, element):
        for xpath in self.url_item.child_xpaths:
            children = element.locator(f'xpath={xpath}').all()
            if children:
                yield children[0]

    def parse(self):
        with self.playwright_context() as context:
            page = context.new_page()
            page.goto(self.url_item.url)
            selector = f'xpath={self.url_item.xpath}'
            self._wait_for_selector(page, selector)
            for element in page.locator(selector).all():
                if self.url_item.child_xpaths:
                    text_elements = list(self._iterate_children(element))
                else:
                    text_elements = [element]
                texts = [r.text_content().strip() for r in text_elements]
                yield self.url_item.text_delimiter.join(
                    [r for r in texts if r])
