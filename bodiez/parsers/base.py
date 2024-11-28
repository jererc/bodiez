from contextlib import contextmanager
import importlib
import inspect
import json
import os

from playwright.sync_api import sync_playwright

from bodiez import WORK_PATH, logger


class BaseParser:
    id = None

    def __init__(self, config):
        self.config = config
        self.work_path = os.path.join(WORK_PATH,
            'parsers', f'.{self.id}')

    @staticmethod
    def can_parse_url(url):
        raise NotImplementedError()

    # @contextmanager
    # def playwright_context(self):
    #     if not os.path.exists(self.work_path):
    #         os.makedirs(self.work_path)
    #     with sync_playwright() as p:
    #         try:
    #             context = p.chromium.launch_persistent_context(
    #                 user_data_dir=self.work_path,
    #                 headless=self.config.HEADLESS,
    #             )
    #             yield context
    #         finally:
    #             context.close()

    @contextmanager
    def playwright_context(self):
        if not os.path.exists(self.work_path):
            os.makedirs(self.work_path)
        state_path = os.path.join(self.work_path, 'state.json')
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=self.config.HEADLESS)
                context = browser.new_context()
                if os.path.exists(state_path):
                    cookies = json.load(open(state_path))['cookies']
                    context.add_cookies(cookies)
                yield context
            finally:
                context.storage_state(path=state_path)
                context.close()

    def parse(self, url):
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
