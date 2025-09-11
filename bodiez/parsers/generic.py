from collections import defaultdict
import logging
import time

from bodiez.parsers.base import BaseParser, Body

logger = logging.getLogger(__name__)


class GenericParser(BaseParser):
    id = 'generic'

    def _find_elements(self, page):
        selector = f'xpath={self.query.xpath}'
        self._wait_for_selector(page, selector)
        if self.query.group_xpath and self.query.group_attrs:
            # Group the base elements then find the target elements using a relative xpath
            groups = defaultdict(list)
            for element in page.locator(selector).all():
                box = element.bounding_box()
                if box:
                    key = tuple(box[r] for r in self.query.group_attrs)
                    groups[key].append(element)
            base_elements = sorted(list(groups.values()), key=lambda x: len(x))[-1]
            res = []
            for element in base_elements:
                elements = element.locator(f'xpath={self.query.group_xpath}').all()
                if not elements:
                    logger.debug(f'no rel elements for {self.query.id=} {element=} {self.query.group_xpath=}')
                    continue
                res.append(elements)
            return res
        else:
            return [[r] for r in page.locator(selector).all()]

    def _validate_element(self, element):
        if self.query.filter_xpath and self.query.filter_callable:
            try:
                val = element.locator(f'xpath={self.query.filter_xpath}').all()[0].text_content().strip()
                return self.query.filter_callable(val)
            except Exception:
                logger.exception(f'Failed to validate {self.query.id=} {element=}')
                self.query.errors.append('failed to validate element')
        return True

    def _iterate_text_elements(self, element):
        for xpath in self.query.text_xpaths:
            try:
                yield element.locator(f'xpath={xpath}').all()[0]
            except IndexError:
                logger.error(f'Failed to find text element for {self.query.id=} {xpath=}')

    def _get_title(self, elements):
        if self.query.text_xpaths:
            text_elements = list(self._iterate_text_elements(elements[0]))
        else:
            text_elements = elements
        texts = [r.text_content().strip() for r in text_elements]
        return self.query.text_delimiter.join(r for r in texts if r)

    def _load_next_page(self, page):
        if self.query.next_page_xpath:
            time.sleep(self.query.navigation_delay)
            try:
                page.locator(f'xpath={self.query.next_page_xpath}').click()
            except Exception as e:
                logger.error(f'failed to click next page {self.query.id=} {self.query.next_page_xpath=}: {e}')
                self._save_page(page, 'failed_to_click_next_page')
                self.query.errors.append('failed to click next page')
                return False
        else:
            page.evaluate('window.scrollBy(0, window.innerHeight)')
            page.wait_for_timeout(self.query.timeout * 1000)
        return True

    def parse(self):
        with self.playwright_context() as context:
            page = self._load_page(context)
            seen_titles = set()
            for i in range(self.query.pages):
                for elements in self._find_elements(page):
                    if not self._validate_element(elements[0]):
                        continue
                    title = self._get_title(elements)
                    if title in seen_titles:
                        continue
                    yield Body(title=title, url=self._get_link(elements[0]))
                    seen_titles.add(title)

                if i < self.query.pages - 1:
                    if not self._load_next_page(page):
                        break
