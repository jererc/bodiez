import logging
import os
from pprint import pprint
import unittest

import bodiez as module
WORK_PATH = os.path.join(os.path.expanduser('~'), '_tests', 'bodiez')
module.WORK_PATH = WORK_PATH
module.logger.setLevel(logging.DEBUG)
module.logger.handlers.clear()
from bodiez import collector
from bodiez.parsers import base


class CleanBodyTestCase(unittest.TestCase):
    def test_1(self):
        body = 'L.A. Noire: The Complete Edition (v2675.1 + All DLCs, MULTi6) [FitGirl Repack]'
        self.assertEqual(collector.clean_body(body), 'L.A. Noire: The Complete Edition')

    def test_2(self):
        body = 'L.A. Noire: The Complete Edition (v2675.1 + All DLCs, MULTi6) [FitGirl...'
        self.assertEqual(collector.clean_body(body), 'L.A. Noire: The Complete Edition')

    def test_3(self):
        body = 'L.A. Noire: The Complete Edition (v2675.1 + All DLCs, ...'
        self.assertEqual(collector.clean_body(body), 'L.A. Noire: The Complete Edition')

    def test_4(self):
        body = 'L.A. Noire (The Complete Edition) (v2675.1 + All DLCs, ...'
        self.assertEqual(collector.clean_body(body), 'L.A. Noire')

    def test_5(self):
        body = 'L.A. Noire [X] (v2675.1 + All DLCs, MULTi6) [FitGirl Repack]'
        self.assertEqual(collector.clean_body(body), 'L.A. Noire')

    def test_6(self):
        body = '[X] L.A. Noire (v2675.1 + All DLCs, MULTi6) [FitGirl Repack]'
        self.assertEqual(collector.clean_body(body), 'L.A. Noire')


class URLItemTestCase(unittest.TestCase):
    def test_1(self):
        urls = [
            'https://1337x.to/user/FitGirl/',
            'https://1337x.to/sort-search/monster%20hunter%20repack/time/desc/1/',
            'https://rutracker.org/forum/tracker.php?f=557',
        ]
        res = [collector.URLItem(url=r) for r in urls]
        for r in res:
            print(r)
        self.assertTrue(all(bool(r.id) for r in res))
        self.assertTrue(all(bool(r.url) for r in res))


class ParsersTestCase(unittest.TestCase):
    def test_1(self):
        res = list(base.iterate_parsers())
        pprint(res)
        self.assertTrue(res)
        self.assertTrue(all(r.id is not None for r in res))
        self.assertTrue(all(issubclass(r, base.BaseParser) for r in res))
