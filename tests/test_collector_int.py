import logging
import os
from pprint import pprint
import shutil
import time
import unittest
from unittest.mock import patch

from svcutils.service import Config

import bodiez as module
WORK_DIR = os.path.join(os.path.expanduser('~'), '_tests', 'bodiez')
module.WORK_DIR = WORK_DIR
module.logger.setLevel(logging.DEBUG)
module.logger.handlers.clear()
from bodiez import collector as module
from bodiez.parsers.base import Body


module.logger.setLevel(logging.DEBUG)


def remove_path(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)


def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


class PreprocessTestCase(unittest.TestCase):
    def test_1(self):
        preprocess = lambda x: str(float(x.replace('$', '').replace(',', '')) * 100 // 10 * 10 / 100)
        res = {preprocess(r) for r in ('$1.07', '$1.08', '$1.11', '$1.19', '$1.29')}
        pprint(res)
        self.assertEqual(len(res), 3)


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # remove_path(WORK_DIR)
        makedirs(WORK_DIR)

    def _collect(self, url, headless=True):
        config = Config(
            __file__,
            STATE_DIR=os.path.join(WORK_DIR, 'state'),
            STORE_DIR=os.path.join(WORK_DIR, 'store'),
            HEADLESS=headless,
        )
        remove_path(config.STORE_DIR)
        return module.Collector(config)._collect_bodies(module.Query(**url))

    def _test_collect(self, *args, **kwargs):
        res = self._collect(*args, **kwargs)
        pprint(res)
        self.assertTrue(res)
        self.assertTrue(all(isinstance(r, Body) for r in res))
        self.assertTrue(len({r.title for r in res}) > len(res) * .9)
        self.assertEqual(len({r.url for r in res}), len(res))
        self.assertTrue(all(r.key is not None for r in res))


class SimpleTestCase(BaseTestCase):
    def test_1337x(self):
        self._test_collect(
            {
                'url': 'https://1337x.to/user/FitGirl/',
                'xpath': '//table/tbody/tr/td[1]/a[2]',
            },
            headless=False,
        )

    def test_1337x_child(self):
        self._test_collect(
            {
                'url': 'https://1337x.to/user/FitGirl/',
                'xpath': '//table/tbody/tr',
                'child_xpaths': [
                    './/td[1]/a[2]',
                ],
                'link_xpath': './/td[1]/a[2]',
            },
            headless=False,
        )

    def test_nvidia(self):
        self._test_collect(
            {
                'url': 'https://www.nvidia.com/en-us/geforce/news/',
                'xpath': '//div[contains(@class, "article-title-text")]/a',
            },
            headless=False,
        )

    def test_nvidia_child(self):
        self._test_collect(
            {
                'url': 'https://www.nvidia.com/en-us/geforce/news/',
                'xpath': '//div[contains(@class, "article-title-text")]',
                'child_xpaths': [
                    './/a',
                ],
                'link_xpath': './/a',
            },
            headless=False,
        )

    def test_lexpress(self):
        self._test_collect(
            {
                'url': 'https://www.lexpressproperty.com/en/buy-mauritius/all/west/?price_max=5000000&currency=MUR&filters%5Binterior_unit%5D%5Beq%5D=m2&filters%5Bland_unit%5D%5Beq%5D=m2',
                'xpath': '//div[contains(@class, "card-row")]',
                'child_xpaths': [
                    './/div[contains(@class, "title-holder")]/h2',
                    './/address',
                    './/div[contains(@class, "card-foot-price")]/strong/a',
                ],
                'link_xpath': './/a',
                'text_delimiter': '\r',
            },
            headless=False,
        )

    def test_rutracker(self):
        self._test_collect(
            {
                'url': 'https://rutracker.org/forum/tracker.php?f=557',
                'xpath': '//div[contains(@class, "t-title")]/a',
                'block_external': True,
            },
            headless=False,
        )

    def test_coinmarketcap_1(self):
        res = self._test_collect(
            {
                'id': 'btc-usd',
                'url': 'https://coinmarketcap.com/currencies/bitcoin/',
                'xpath': '//span[@data-test="text-cdp-price-display"]',
                'block_external': True,
                'key_processor': lambda x: str(float(x.replace('$', '').replace(',', '')) // 1000 * 1000),
            },
            headless=False,
        )

    def test_coinmarketcap_2(self):
        res = self._test_collect(
            {
                'id': 'ada-usd',
                'url': 'https://coinmarketcap.com/currencies/cardano/',
                'xpath': '//span[@data-test="text-cdp-price-display"]',
                'block_external': True,
                'key_processor': lambda x: str(float(x.replace('$', '').replace(',', '')) * 100 // 10 / 10),
            },
            headless=False,
        )


class GenericTestCase(BaseTestCase):
    def test_fb_marketplace(self):
        self._test_collect(
            {
                'url': 'https://www.facebook.com/marketplace/108433389181024/propertyforsale',
                'id': 'property-for-sale',
                'xpath': '//img',
                'group_attrs': ['width', 'height'],
                'rel_xpath': '../../../../../../../div[2]/div',
                'link_xpath': '../../../../../../../..',
                'pages': 1,
            },
            headless=False,
        )

    def test_fb_marketplace_child(self):
        self._test_collect(
            {
                'url': 'https://www.facebook.com/marketplace/108433389181024/propertyforsale',
                'id': 'property-for-sale',
                'xpath': '//img',
                'group_attrs': ['width', 'height'],
                'rel_xpath': '../../../../../../../div[2]',
                'child_xpaths': [
                    './/div[1]',
                    './/div[3]',
                ],
                'link_xpath': '../../../../../../../..',
                'pages': 1,
            },
            headless=False,
        )

    def test_fb_timeline(self):
        self._test_collect(
            {
                'url': 'https://www.facebook.com/iqonmauritius',
                'id': 'iqon',
                'xpath': '//*[local-name()="svg"][@aria-label]',
                'group_attrs': ['x'],
                'rel_xpath': '../../../../../../../../div[3]/div[1]',
                'link_xpath': '../../../../../../../../div[3]/div[2]/*/a',
                'pages': 3,
            },
            headless=False,
        )

    def test_fb_timeline_child(self):
        self._test_collect(
            {
                'url': 'https://www.facebook.com/iqonmauritius',
                'id': 'iqon',
                'xpath': '//*[local-name()="svg"][@aria-label]',
                'group_attrs': ['x'],
                'rel_xpath': '../../../../../../../../div[3]',
                'child_xpaths': [
                    './/div[1]',
                ],
                'link_xpath': '../../../../../../../../div[3]/div[2]/*/a',
                'pages': 3,
            },
            headless=False,
        )


class TimeoutTestCase(BaseTestCase):
    def test_timeout(self):
        self.assertRaises(Exception, self._collect,
            {
                'url': 'https://1337x.to/user/FitGirl/',
                'xpath': '//table/tbody/tr/td[999]/a[999]',
            },
            headless=True,
        )

    def test_no_result(self):
        res = self._collect(
            {
                'url': 'https://1337x.to/search/asdasdasd/1/',
                'xpath': '//table/tbody/tr/td[1]/a[2]',
                'allow_no_results': True,
            },
            headless=True,
        )
        self.assertEqual(res, [])


class WorkflowTestCase(BaseTestCase):
    def test_1(self):
        config = Config(
            __file__,
            QUERIES=[
                {
                    'url': 'https://1337x.to/user/FitGirl/',
                    'xpath': '//table/tbody/tr/td[1]/a[2]',
                    'update_delta': 0,
                },
            ],
            STATE_DIR=os.path.join(WORK_DIR, 'state'),
            STORE_DIR=os.path.join(WORK_DIR, 'store'),
        )
        remove_path(config.STORE_DIR)
        collector = module.Collector(config)

        def run():
            time.sleep(.01)
            collector.run()

        doc = collector.store.get(config.QUERIES[0]['url'])
        pprint(doc)
        self.assertFalse(doc.keys)

        with patch.object(module.Notifier, 'send') as mock_send:
            run()
        pprint(mock_send.call_args_list)
        self.assertEqual(len(mock_send.call_args_list), 4)

        doc = collector.store.get(config.QUERIES[0]['url'])
        pprint(doc)
        self.assertTrue(doc.keys)

        with patch.object(module.Notifier, 'send') as mock_send:
            run()
        pprint(mock_send.call_args_list)
        self.assertFalse(mock_send.call_args_list)

        new_titles = [f'body {i}' for i in range(2)]
        with patch.object(module.Notifier, 'send') as mock_send, \
                patch.object(collector,
                    '_collect_bodies') as mock__collect_bodies:
            mock__collect_bodies.return_value = [Body(title=r, key=r)
                for r in (new_titles + doc.keys[:-len(new_titles)])]
            run()
        pprint(mock_send.call_args_list)
        prev_doc_keys = doc.keys
        doc = collector.store.get(config.QUERIES[0]['url'])
        pprint(doc)
        self.assertEqual(doc.keys, new_titles + prev_doc_keys)
