from collections import defaultdict

from bodiez.parsers.base import BaseParser


class ScrollingParser(BaseParser):
    id = 'scrolling'

    def can_parse(self):
        return (bool(self.url_item.scroll_xpath)
            and bool(self.url_item.rel_xpath))

    def _get_elements(self, page):
        selector = f'xpath={self.url_item.scroll_xpath}'
        self._wait_for_selector(page, selector)
        groups = defaultdict(list)
        attrs = self.url_item.scroll_group_attrs
        for element in page.locator(selector).all():
            box = element.bounding_box()
            if box:
                groups[tuple(box[r] for r in attrs)].append(element)
        return sorted(list(groups.values()), key=lambda x: len(x))[-1]

    def _iterate_children(self, element):
        for xpath in self.url_item.child_xpaths:
            children = element.locator(f'xpath={xpath}').all()
            if children:
                yield children[0]

    def _scroll(self, page):
        page.evaluate('window.scrollBy(0, window.innerHeight)')
        page.wait_for_timeout(2000)

    def parse(self):
        with self.playwright_context() as context:
            page = context.new_page()
            page.goto(self.url_item.url)
            rel_selector = f'xpath={self.url_item.rel_xpath}'
            seen_titles = set()
            for i in range(self.url_item.max_scrolls):
                for element in self._get_elements(page):
                    rel_elements = element.locator(rel_selector).all()
                    if not rel_elements:
                        continue
                    if self.url_item.child_xpaths:
                        text_elements = list(self._iterate_children(
                            rel_elements[0]))
                    else:
                        text_elements = rel_elements
                    texts = [r.text_content().strip() for r in text_elements]
                    title = self.url_item.text_delimiter.join(
                        [r for r in texts if r])
                    if title not in seen_titles:
                        yield title
                        seen_titles.add(title)
                if i < self.url_item.max_scrolls - 1:
                    self._scroll(page)
