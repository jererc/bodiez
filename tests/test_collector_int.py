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
        return module.Collector(config)._collect_bodies(module.Query(**query_dict))

    def _test_collect(self, *args, **kwargs):
        res = self._collect(*args, **kwargs)
        pprint(res)
        self.assertTrue(res, 'no results')
        self.assertTrue(all(isinstance(r, Body) for r in res), 'invalid results')
        self.assertTrue(len({r.title for r in res}) > len(res) * .9, 'invalid titles')
        self.assertTrue(len({r.url for r in res}) > len(res) * .9, 'invalid urls')
        self.assertTrue(all(r.key is not None for r in res), 'invalid keys')


class DefaultTestCase(BaseTestCase):
    def setUp(self):
        os.makedirs(WORK_DIR, exist_ok=True)
        self.settings_file = os.path.join(os.path.dirname(os.path.dirname(module.__file__)), 'bootstrap', 'user_settings.py')
        config = Config(self.settings_file)
        self.query_dicts = config.QUERIES
        ids = [q['id'] for q in self.query_dicts]
        assert len(set(ids)) == len(ids)

    def test_all(self):
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


class GenericTestCase(BaseTestCase):
    def test_fb_marketplace(self):
        self._test_collect(
            {
                'url': 'https://www.facebook.com/marketplace/108433389181024/propertyforsale',
                'id': 'property-for-sale',
                'xpath': '//img',
                'group_attrs': ['width', 'height'],
                'rel_xpath': '../../../../../../../div[2]/div',
                'link_xpath': '../../..',
                'pages': 1,
            },
            headless=False,
        )

    def test_fb_marketplace_text_xpaths(self):
        self._test_collect(
            {
                'url': 'https://www.facebook.com/marketplace/108433389181024/propertyforsale',
                'id': 'property-for-sale',
                'xpath': '//img',
                'group_attrs': ['width', 'height'],
                'rel_xpath': '../../../../../../../div[2]',
                'text_xpaths': [
                    './/div[1]',
                    './/div[3]',
                ],
                'link_xpath': '../..',
                'pages': 1,
            },
            headless=False,
        )

    def test_fb_posts(self):
        self._test_collect(
            {
                'url': 'https://www.facebook.com/iqonmauritius',
                'id': 'iqon',
                'xpath': '//*[local-name()="svg"][@aria-label]',
                'group_attrs': ['x'],
                'rel_xpath': '../../../../../../../../../div[3]/div[1]',
                'link_xpath': '../div[2]//a',
                'pages': 3,
            },
            headless=False,
        )


class LoginTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        remove_path(os.path.join(WORK_DIR, 'state'))

    def test_fb_login(self):
        self._test_collect(
            {
                'url': 'https://www.facebook.com/marketplace/108433389181024/propertyforsale',
                'id': 'property-for-sale',
                'xpath': '//img',
                'login_xpath': '//input[@name="email"]',
                'group_attrs': ['width', 'height'],
                'rel_xpath': '../../../../../../../div[2]/div',
                'link_xpath': '../../..',
                'pages': 1,
            },
            headless=False,
        )


class FilterTestCase(BaseTestCase):
    def test_1337x(self):
        self._test_collect(
            {
                'url': 'https://1337x.to/user/FitGirl/',
                'xpath': '//table/tbody/tr/td[1]/a[2]',
                'filter_xpath': '../../td[3]',
                'filter_callable': lambda x: int(x) > 50,
            },
            headless=False,
        )

    def test_1337x_child(self):
        self._test_collect(
            {
                'url': 'https://1337x.to/user/FitGirl/',
                'xpath': '//table/tbody/tr',
                'text_xpaths': [
                    './/td[1]/a[2]',
                ],
                'link_xpath': './/td[1]/a[2]',
                'filter_xpath': './/td[3]',
                'filter_callable': lambda x: int(x) > 50,
            },
            headless=False,
        )


class TimeoutTestCase(BaseTestCase):
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
