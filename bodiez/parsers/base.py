from contextlib import contextmanager
import importlib
import inspect
import os
import pkgutil
from urllib.parse import urlparse

from playwright.sync_api import TimeoutError, sync_playwright

from bodiez import WORK_DIR, logger


BASE_STATE_DIRNAME = 'state'


def get_url_domain_name(url):
    parts = urlparse(url).netloc.split('.')
    out_parts = parts[1:] if parts[0] == 'www' else parts
    return '.'.join(out_parts[:-1])


class BaseParser:
    id = None

    def __init__(self, config, url_item):
        self.config = config
        self.url_item = url_item
        self.state_dir = os.path.join(WORK_DIR, BASE_STATE_DIRNAME,
            self._get_state_dirname())
        self.timeout = 10000 if self.config.HEADLESS else 120000

    def _get_state_dirname(self):
        return urlparse(self.url_item.url).netloc

    def _is_external_domain(self, request):
        return (get_url_domain_name(self.url_item.url)
            not in urlparse(request.url).netloc.split('.'))

    def _request_handler(self, route, request):
        if self.url_item.block_external and self._is_external_domain(request):
            route.abort()
            return
        if self.url_item.block_images and request.resource_type == 'image':
            route.abort()
            return
        route.continue_()

    @contextmanager
    def playwright_context(self):
        if not os.path.exists(self.state_dir):
            os.makedirs(self.state_dir)
        state_path = os.path.join(self.state_dir, 'state.json')
        with sync_playwright() as p:
            try:
                browser = p.webkit.launch(
                    headless=self.config.HEADLESS,
                    args=[
                        # '--disable-blink-features=AutomationControlled',
                    ],
                )
                context = browser.new_context(storage_state=state_path
                    if os.path.exists(state_path) else None)
                context.route('**/*', self._request_handler)
                yield context
            finally:
                context.storage_state(path=state_path)
                context.close()

    def _wait_for_selector(self, page, selector):
        try:
            page.wait_for_selector(selector, timeout=self.timeout)
        except TimeoutError:
            if not self.url_item.allow_no_results:
                raise Exception('timeout')
            logger.debug(f'timed out for {selector}')

    def can_parse(self):
        raise NotImplementedError()

    def parse(self):
        raise NotImplementedError()


# def iterate_parsers(package_name='bodiez.parsers'):
#     package = importlib.import_module(package_name)
#     for _, module_name, ispkg in pkgutil.iter_modules(package.__path__):
#         module = importlib.import_module(f'{package_name}.{module_name}')
#         for name, obj in inspect.getmembers(module, inspect.isclass):
#             if issubclass(obj, BaseParser) and obj is not BaseParser:
#                 yield obj
