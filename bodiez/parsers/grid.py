from collections import defaultdict

from bodiez.parsers.base import BaseParser


class GridParser(BaseParser):
    id = 'grid'

    def can_parse(self):
        return bool(self.url_item.grid_xpath)

    def _get_grid_elements(self, page):
        selector = f'xpath={self.url_item.grid_xpath}'
        self._wait_for_selector(page, selector)
        grids = defaultdict(list)
        for element in page.locator(selector).all():
            box = element.bounding_box()
            if box:
                grids[f'{box["width"]}x{box["height"]}'].append(element)
        return sorted([r for r in grids.values()], key=lambda x: len(x))[-1]

    def parse(self):
        with self.playwright_context() as context:
            page = context.new_page()
            page.goto(self.url_item.url)
            selector = f'xpath={self.url_item.grid_xpath}'
            self._wait_for_selector(page, selector)
            rel_selector = f'xpath={self.url_item.grid_rel_xpath}'
            for element in self._get_grid_elements(page):
                rel_element = element.locator(rel_selector).all()
                texts = [r.text_content().strip() for r in rel_element]
                yield self.url_item.multi_element_delimiter.join(
                    [r for r in texts if r])
