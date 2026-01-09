import os
from pprint import pprint, pformat
import shutil
import time
import unittest
from unittest.mock import patch

from svcutils.service import Config

from tests import WORK_DIR
from bodiez import collector as module
from bodiez.parsers.base import Body


def remove_path(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        # remove_path(WORK_DIR)
        os.makedirs(WORK_DIR, exist_ok=True)

    def _collect(self, query_dict, headless=True):
        config = Config(
            __file__,
            STATE_DIR=os.path.join(WORK_DIR, 'state'),
            STORE_DIR=os.path.join(WORK_DIR, 'store'),
            HEADLESS=headless,
        )
        remove_path(config.STORE_DIR)
        query = module.Query(**query_dict)
        return module.Collector(config)._collect_bodies(query), query

    def _test_collect(self, *args, **kwargs):
        bodies, query = self._collect(*args, **kwargs)
        # pprint(bodies)
        self.assertTrue(bodies, 'no results')
        self.assertTrue(all(isinstance(r, Body) for r in bodies), 'invalid results')
        self.assertTrue(len({r.title for r in bodies}) > len(bodies) * .9, 'invalid titles')
        self.assertTrue(len({r.url for r in bodies}) > len(bodies) * .9, 'invalid urls')
        self.assertTrue(all(r.key is not None for r in bodies), 'invalid keys')
        self.assertEqual(query.errors, [])


class CollectTestCase(BaseTestCase):
    def setUp(self):
        os.makedirs(WORK_DIR, exist_ok=True)
        self.settings_file = os.path.join(os.path.dirname(os.path.dirname(module.__file__)), 'bootstrap', 'user_settings.py')
        config = Config(self.settings_file)
        self.query_dicts = config.QUERIES
        ids = [q['id'] for q in self.query_dicts]
        assert len(set(ids)) == len(ids)

    def test_default_queries(self):
        results = {}
        for query_dict in self.query_dicts:
            try:
                self._test_collect(query_dict, headless=False)
            except Exception as e:
                results[query_dict['id']] = {
                    'success': False,
                    'message': str(e),
                }
            else:
                results[query_dict['id']] = {
                    'success': True,
                    'message': None,
                }
        pprint(results)
        failures = {k: v['message'] for k, v in results.items() if not v['success']}
        self.assertFalse(failures, pformat(failures))

    def test_1337x(self):
        self._test_collect(
            {
                'url': 'https://1337x.to/user/FitGirl/',
                'xpath': '//table/tbody/tr/td[1]/a[2]',
                'filter_xpath': '../../td[3]',
                'filter_callable': lambda x: int(x) > 50,
                'next_page_xpath': '//a[contains(text(), ">>")]',
                'pages': 3,
            },
            headless=False,
        )

    def test_fitgirl(self):
        self._test_collect(
            {
                'url': 'https://fitgirl-repacks.site/category/lossless-repack/',
                'block_external': True,
                'xpath': '//article/header/h1/a',
                'next_page_xpath': '//a[contains(text(), "Next →")]',
                'pages': 3,
            },
            headless=False,
        )

    def test_fb_marketplace(self):
        self._test_collect(
            {
                'url': 'https://www.facebook.com/marketplace/108433389181024/propertyforsale',
                'id': 'property-for-sale',
                'xpath': '//img',
                'group_xpath': '../../../../../../../div[2]/div',
                'group_attrs': ['width', 'height'],
                'link_xpath': '../../..',
            },
            headless=False,
        )

    def test_fb_marketplace_text_xpaths(self):
        self._test_collect(
            {
                'url': 'https://www.facebook.com/marketplace/108433389181024/propertyforsale',
                'id': 'property-for-sale',
                'xpath': '//img',
                'group_xpath': '../../../../../../../div[2]',
                'group_attrs': ['width', 'height'],
                'text_xpaths': [
                    './div[1]',   # price
                    # './div[2]',   # title
                    './div[3]',   # location
                ],
                'link_xpath': '../..',
                'pages': 2,
            },
            headless=False,
        )

    def test_fb_posts(self):
        self._test_collect(
            {
                'url': 'https://www.facebook.com/iqonmauritius',
                'id': 'iqon',
                'xpath': '//*[local-name()="svg"][@aria-label]',
                'group_xpath': '../../../../../../../../../div[3]/div[1]',
                'group_attrs': ['x'],
                'link_xpath': '../div[2]//a',
                'pages': 3,
            },
            headless=False,
        )

    def test_kitesurfmu(self):
        self._test_collect(
            {
                'url': 'https://kitesurf.mu/index.php?id_category=902&controller=category&id_lang=1',
                'id': 'surf-top',
                'xpath': '//div[@class="product-miniature-information"]',
                'text_xpaths': [
                    './/a',
                    './/span[@class="price"]',
                ],
                'link_xpath': './/a',
                'next_page_xpath': '//a[@rel="next" and not(contains(@class, "disabled"))]',
                'pages': 10,
                'block_external': True,
                'update_delta': 8 * 3600,
                'max_notif': 10,
            },
            headless=False,
        )

    def test_timeout(self):
        self.assertRaises(
            Exception,
            self._collect,
            {
                'url': 'https://1337x.to/user/FitGirl/',
                'xpath': '//table/tbody/tr/td[999]/a[999]',
            },
            headless=True,
        )

    def test_no_result(self):
        bodies, query = self._collect(
            {
                'url': 'https://1337x.to/search/asdasdasd/1/',
                'xpath': '//table/tbody/tr/td[1]/a[2]',
                'allow_no_results': True,
            },
            headless=True,
        )
        self.assertEqual(bodies, [])
        self.assertEqual(query.errors, [])


class LoginTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        remove_path(os.path.join(WORK_DIR, 'state'))

    def test_rutracker(self):
        self._test_collect(
            {
                'url': 'https://rutracker.org/forum/tracker.php?f=557',
                'id': 'rutracker',
                'login_xpath': '//input[@name="login_username"]',
                'xpath': '//div[contains(@class, "t-title")]/a',
                'block_external': True,
            },
            headless=False,
        )

    def test_fb(self):
        self._test_collect(
            {
                'url': 'https://www.facebook.com/marketplace/108433389181024/propertyforsale',
                'id': 'property-for-sale',
                'login_xpath': '//input[@name="email"]',
                'xpath': '//img',
                'group_xpath': '../../../../../../../div[2]/div',
                'group_attrs': ['width', 'height'],
                'link_xpath': '../../..',
            },
            headless=False,
        )


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

        with patch.object(module, 'notify') as mock_notify:
            run()
        pprint(mock_notify.call_args_list)
        self.assertEqual(len(mock_notify.call_args_list), 4)

        doc = collector.store.get(config.QUERIES[0]['url'])
        pprint(doc)
        self.assertTrue(doc.keys)

        with patch.object(module, 'notify') as mock_notify:
            run()
        pprint(mock_notify.call_args_list)
        self.assertFalse(mock_notify.call_args_list)

        new_titles = [f'body {i}' for i in range(2)]
        with patch.object(module, 'notify') as mock_notify, \
                patch.object(collector, '_collect_bodies') as mock__collect_bodies:
            mock__collect_bodies.return_value = [Body(title=r, key=r)
                                                 for r in (new_titles + doc.keys[:-len(new_titles)])]
            run()
        pprint(mock_notify.call_args_list)
        prev_doc_keys = doc.keys
        doc = collector.store.get(config.QUERIES[0]['url'])
        pprint(doc)
        self.assertEqual(doc.keys, new_titles + prev_doc_keys)
