from collections import defaultdict
import logging
import time

from bodiez.parsers.base import BaseParser, Body


logger = logging.getLogger(__name__)


class GenericParser(BaseParser):
    id = 'generic'

    def _check_login(self, page):
        def check_login():
            try:
                return not page.locator(f'xpath={self.query.login_xpath}').all()
            except Exception as e:
                logger.debug(f'failed to check login {self.query.id=}: {e}')
                return False

        if not self.query.login_xpath:
            return
        if check_login():
            return
        if self.config.HEADLESS:
            raise Exception('Interactive login required')
        logger.debug('waiting for login...')
        while not check_login():
            time.sleep(5)

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

    def _validate_element(self, element):
        if self.query.filter_xpath and self.query.filter_callable:
            try:
                val = element.locator(f'xpath={self.query.filter_xpath}').all()[0].text_content().strip()
                return self.query.filter_callable(val)
            except Exception:
                logger.exception(f'Failed to validate {self.query.id=} {element=}')
                return True
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
        page.evaluate('window.scrollBy(0, window.innerHeight)')
        page.wait_for_timeout(2000)

    def parse(self):
        with self.playwright_context() as context:
            page = self._load_page(context)
            self._check_login(page)
            seen_titles = set()
            for i in range(self.query.pages):
                for element in self._find_elements(page):
                    if self.query.rel_xpath:
                        rel_elements = element.locator(f'xpath={self.query.rel_xpath}').all()
                        if not rel_elements:
                            logger.debug(f'no rel elements for {self.query.id=} {element=} {self.query.rel_xpath=}')
                            continue
                    else:
                        rel_elements = [element]
                    if not self._validate_element(rel_elements[0]):
                        continue
                    title = self._get_title(rel_elements)
                    if title in seen_titles:
                        continue
                    yield Body(title=title, url=self._get_link(rel_elements[0]))
                    seen_titles.add(title)
                if i < self.query.pages - 1:
                    self._load_next_page(page)
