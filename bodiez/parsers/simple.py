from bodiez.parsers.base import BaseParser, Body


class SimpleParser(BaseParser):
    id = 'simple'

    def can_parse(self):
        return bool(self.query.xpath)

    def _iterate_children(self, element):
        for xpath in self.query.child_xpaths:
            children = element.locator(f'xpath={xpath}').all()
            if children:
                yield children[0]

    def parse(self):
        with self.playwright_context() as context:
            page = context.new_page()
            page.goto(self.query.url)
            selector = f'xpath={self.query.xpath}'
            self._wait_for_selector(page, selector)
            for element in page.locator(selector).all():
                if self.query.child_xpaths:
                    text_elements = list(self._iterate_children(element))
                else:
                    text_elements = [element]
                texts = [r.text_content().strip() for r in text_elements]
                title = self.query.text_delimiter.join(
                    [r for r in texts if r])
                yield Body(title=title, url=self._get_link(element))
