from collections import defaultdict

from bodiez.parsers.base import BaseParser, Body


class GenericParser(BaseParser):
    id = 'generic'

    def _find_elements(self, page):
        selector = f'xpath={self.query.xpath}'
        self._wait_for_selector(page, selector)
        if not self.query.group_attrs:
            return page.locator(selector).all()
        groups = defaultdict(list)
        for element in page.locator(selector).all():
            box = element.bounding_box()
            if box:
                key = tuple(box[r] for r in self.query.group_attrs)
                groups[key].append(element)
        return sorted(list(groups.values()), key=lambda x: len(x))[-1]

    def _iterate_children(self, element):
        for xpath in self.query.child_xpaths:
            children = element.locator(f'xpath={xpath}').all()
            if children:
                yield children[0]

    def _load_next_page(self, page):
        page.evaluate('window.scrollBy(0, window.innerHeight)')
        page.wait_for_timeout(2000)

    def parse(self):
        with self.playwright_context() as context:
            page = self._load_page(context)
            rel_selector = (f'xpath={self.query.rel_xpath}'
                if self.query.rel_xpath else None)
            seen_titles = set()
            for i in range(self.query.pages):
                for element in self._find_elements(page):
                    if rel_selector:
                        rel_elements = element.locator(rel_selector).all()
                        if not rel_elements:
                            continue
                    else:
                        rel_elements = [element]
                    if self.query.child_xpaths:
                        text_elements = list(self._iterate_children(
                            rel_elements[0]))
                    else:
                        text_elements = rel_elements
                    texts = [r.text_content().strip() for r in text_elements]
                    title = self.query.text_delimiter.join(
                        [r for r in texts if r])
                    if title in seen_titles:
                        continue
                    yield Body(title=title, url=self._get_link(element))
                    seen_titles.add(title)
                if i < self.query.pages - 1:
                    self._load_next_page(page)
