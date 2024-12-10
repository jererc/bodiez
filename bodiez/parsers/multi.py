from bodiez.parsers.base import BaseParser


class MultiElementParser(BaseParser):
    id = 'multi_element'

    def can_parse(self):
        return (bool(self.url_item.parent_xpath)
            and bool(self.url_item.child_xpaths))

    def parse(self):
        with self.playwright_context() as context:
            page = context.new_page()
            page.goto(self.url_item.url)
            selector = f'xpath={self.url_item.parent_xpath}'
            self._wait_for_selector(page, selector)
            for element in page.locator(selector).element_handles():
                children = [element.query_selector(f'xpath={r}')
                    for r in self.url_item.child_xpaths]
                yield self.url_item.multi_element_delimiter.join(
                    [r.text_content().strip() if r else 'NULL'
                        for r in children])
