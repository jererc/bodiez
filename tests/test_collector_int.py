import logging
import os
from pprint import pprint
import shutil
import time
import unittest
from unittest.mock import patch

from svcutils.service import Config

import bodiez as module
WORK_PATH = os.path.join(os.path.expanduser('~'), '_tests', 'bodiez')
module.WORK_PATH = WORK_PATH
module.logger.setLevel(logging.DEBUG)
module.logger.handlers.clear()
from bodiez import collector as module
from bodiez.store import Firestore


GOOGLE_CREDS = os.path.join(os.path.expanduser('~'), 'gcs-bodiez.json')

module.logger.setLevel(logging.DEBUG)


def remove_path(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)


def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # remove_path(WORK_PATH)
        makedirs(WORK_PATH)

    def _reset_storage(self, config):
        fs = Firestore(config)
        print(f'deleting all documents in firestore collection '
            f'{config.FIRESTORE_COLLECTION}...')
        for doc in fs.col.list_documents():
            doc.delete()
        remove_path(config.SHARED_STORE_PATH)

    def _collect(self, url, headless=True):
        config = Config(
            __file__,
            SHARED_STORE_PATH=os.path.join(WORK_PATH, 'bodiez'),
            GOOGLE_CREDS=None,
            FIRESTORE_COLLECTION='test',
            MIN_BODIES_HISTORY=10,
            HEADLESS=headless,
        )
        remove_path(config.SHARED_STORE_PATH)
        res = module.Collector(config)._collect_bodies(module.URLItem(**url))
        self.assertTrue(res)


class GenericTestCase(BaseTestCase):
    def test_1337x(self):
        self._collect(
            {
                'url': 'https://1337x.to/user/FitGirl/',
                'params': {
                    'xpath': '//table/tbody/tr/td[1]/a[2]',
                },
            },
            headless=False,
        )

        self._collect(
            {
                'url': 'https://1337x.to/user/FitGirl/',
                'params': {
                    'parent_xpath': '//table/tbody/tr',
                    'children_xpaths': [
                        './/td[1]/a[2]',
                    ],
                },
            },
            headless=False,
        )

    def test_nvidia(self):
        self._collect(
            {
                'url': 'https://www.nvidia.com/en-us/geforce/news/',
                'params': {
                    'xpath': '//div[contains(@class, "article-title-text")]/a',
                },
            },
            headless=False,
        )

        self._collect(
            {
                'url': 'https://www.nvidia.com/en-us/geforce/news/',
                'params': {
                    'parent_xpath': '//div[contains(@class, "article-title-text")]',
                    'children_xpaths': [
                        './/a',
                    ],
                },
            },
            headless=False,
        )

    def test_lexpress(self):
        self._collect(
            {
                'url': 'https://www.lexpressproperty.com/en/buy-mauritius/all/west/?price_max=5000000&currency=MUR&filters%5Binterior_unit%5D%5Beq%5D=m2&filters%5Bland_unit%5D%5Beq%5D=m2',
                'params': {
                    'parent_xpath': '//div[contains(@class, "card-row")]',
                    'children_xpaths': [
                        './/div[contains(@class, "title-holder")]/h2',
                        './/address',
                        './/div[contains(@class, "card-foot-price")]/strong/a',
                    ],
                },
            },
            headless=False,
        )

    def test_rutracker(self):
        self._collect(
            {
                'url': 'https://rutracker.org/forum/tracker.php?f=557',
                'params': {
                    'xpath': '//div[contains(@class, "t-title")]/a',
                },
            },
            headless=False,
        )


class RutrackerTestCase(BaseTestCase):
    def test_ok(self):
        self._collect(
            {
                'url': 'https://rutracker.org/forum/tracker.php?f=557',
            },
            headless=False,
        )


class WorkflowTestCase(BaseTestCase):
    def test_1(self):
        config = Config(
            __file__,
            URLS=[
                {
                    'url': 'https://1337x.to/user/FitGirl/',
                    'update_delta': 0,
                },
            ],
            SHARED_STORE_PATH=os.path.join(WORK_PATH, 'bodiez'),
            GOOGLE_CREDS=GOOGLE_CREDS,
            FIRESTORE_COLLECTION='test',
            MIN_BODIES_HISTORY=10,
        )
        self._reset_storage(config)
        collector = module.Collector(config)

        def run():
            time.sleep(.01)
            collector.run()

        doc = collector.store.get(config.URLS[0]['url'])
        pprint(doc)
        self.assertFalse(doc.bodies)

        with patch.object(module.Notifier, 'send') as mock_send:
            run()
        pprint(mock_send.call_args_list)
        self.assertEqual(len(mock_send.call_args_list),
            module.MAX_NOTIF_PER_URL)

        doc = collector.store.get(config.URLS[0]['url'])
        pprint(doc)
        self.assertTrue(doc.bodies)

        with patch.object(module.Notifier, 'send') as mock_send:
            run()
        pprint(mock_send.call_args_list)
        self.assertFalse(mock_send.call_args_list)

        new_bodies = [f'body {i}' for i in range(2)]
        with patch.object(module.Notifier, 'send') as mock_send, \
                patch.object(collector,
                    '_collect_bodies') as mock__collect_bodies:
            mock__collect_bodies.return_value = (new_bodies
                + doc.bodies[:-len(new_bodies)])
            run()
        pprint(mock_send.call_args_list)
        prev_doc_bodies = doc.bodies
        doc = collector.store.get(config.URLS[0]['url'])
        pprint(doc)
        self.assertEqual(doc.bodies, new_bodies + prev_doc_bodies)
