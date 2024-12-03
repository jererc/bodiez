from contextlib import contextmanager
import importlib
import inspect
import os
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from bodiez import WORK_PATH, logger


def get_url_domain_name(url):
    parts = urlparse(url).netloc.split('.')
    out_parts = parts[1:] if parts[0] == 'www' else parts
    return '.'.join(out_parts[:-1])


class BaseParser:
    id = None

    def __init__(self, config, url_item):
        self.config = config
        self.url_item = url_item
        self.work_path = os.path.join(WORK_PATH, 'parsers',
            self._get_state_dirname())
        self.timeout = 10000 if self.config.HEADLESS else 120000

    def _get_state_dirname(self):
        return urlparse(self.url_item.url).netloc

    def _validate_domain(self, request):
        return (get_url_domain_name(self.url_item.url)
            in urlparse(request.url).netloc.split('.'))

    def _request_handler(self, route, request):
        if self.url_item.block_external and not self._validate_domain(request):
            route.abort()
            return
        if self.url_item.block_images and request.resource_type == 'image':
            route.abort()
            return
        route.continue_()

    @contextmanager
    def playwright_context(self):
        if not os.path.exists(self.work_path):
            os.makedirs(self.work_path)
        state_path = os.path.join(self.work_path, 'state.json')
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(
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

    def can_parse(self):
        raise NotImplementedError()

    def parse(self):
        raise NotImplementedError()


def iterate_parsers(package='bodiez.parsers'):
    for filename in os.listdir(os.path.dirname(os.path.realpath(__file__))):
        basename, ext = os.path.splitext(filename)
        if ext == '.py' and not filename.startswith('__'):
            module_name = f'{package}.{basename}'
            try:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseParser) and obj is not BaseParser:
                        yield obj
            except ImportError as exc:
                logger.error(f'failed to import {module_name}: {exc}')
