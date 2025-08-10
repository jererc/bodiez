from dataclasses import dataclass
from contextlib import contextmanager
import importlib
import inspect
import logging
import os
import pkgutil
import time
from urllib.parse import urljoin, urlparse

from playwright.sync_api import TimeoutError
from webutils.browser import State, playwright_context, save_page

from bodiez import WORK_DIR


logger = logging.getLogger(__name__)


def get_url_domain_name(url):
    parts = urlparse(url).netloc.split('.')
    out_parts = parts[1:] if parts[0] == 'www' else parts
    return '.'.join(out_parts[:-1])


@dataclass
class Body:
    title: str
    url: str = None
    key: str = None


class BaseParser:
    id = None

    def __init__(self, config, query):
        self.config = config
        self.query = query
        self.state = State(os.path.join(self.config.STATE_DIR, f'{urlparse(self.query.url).netloc}.json'))
        self.timeout = self.query.headless_timeout if self.config.HEADLESS else self.query.headful_timeout

    def _is_external_domain(self, request):
        return get_url_domain_name(self.query.url) not in urlparse(request.url).netloc.split('.')

    def _request_handler(self, route, request):
        if self.query.block_external and self._is_external_domain(request):
            route.abort()
            return
        if self.query.block_images and request.resource_type == 'image':
            route.abort()
            return
        route.continue_()

    @contextmanager
    def playwright_context(self):
        with playwright_context(self.state, self.config.HEADLESS) as context:
            context.route('**/*', self._request_handler)
            yield context

    def _save_page(self, page, name):
        save_page(page, os.path.join(WORK_DIR, 'debug'), name)

    def _load_page(self, context):
        page = context.new_page()
        page.goto(self.query.url)
        if self.config.LOGIN_TIMEOUT and not self.config.HEADLESS:
            logger.debug(f'waiting {self.config.LOGIN_TIMEOUT} seconds for login...')
            time.sleep(self.config.LOGIN_TIMEOUT)
        return page

    def _wait_for_selector(self, page, selector):
        logger.debug(f'waiting {self.timeout} seconds for {selector}')
        try:
            page.wait_for_selector(selector, timeout=self.timeout * 1000)
        except TimeoutError:
            self._save_page(page, 'selector_not_found')
            if not self.query.allow_no_results:
                raise Exception('timeout')
            logger.debug(f'timed out for {selector}')

    def _get_link(self, element):
        if not self.query.link_xpath:
            return self.query.url
        links = element.locator(f'xpath={self.query.link_xpath}').all()
        if not links:
            return self.query.url
        val = links[0].get_attribute('href')
        if not val:
            return self.query.url
        if val.startswith('http'):
            return val
        parsed = urlparse(self.query.url)
        return urljoin(f'{parsed.scheme}://{parsed.netloc}/{parsed.path}', val)

    def _print_element(self, element):
        content = element.evaluate('element => element.outerHTML')
        try:
            from bs4 import BeautifulSoup
            print(BeautifulSoup(content, 'html.parser').prettify())
        except ImportError:
            print(content)

    def parse(self):
        raise NotImplementedError()


def iterate_parsers(package_name='bodiez.parsers'):
    package = importlib.import_module(package_name)
    for _, module_name, ispkg in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f'{package_name}.{module_name}')
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseParser) and obj.id:
                yield obj
