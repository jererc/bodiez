import logging
import os
from pprint import pprint
import unittest

import bodiez as module
WORK_DIR = os.path.join(os.path.expanduser('~'), '_tests', 'bodiez')
module.WORK_DIR = WORK_DIR
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

    def test_7(self):
        body = "Anton Bruckner - Symphonie Nr. 7 / Symphony No. 7 (Gewandhausorchester Leipzig - Franz Konwitschny) / \u0410\u043d\u0442\u043e\u043d \u0411\u0440\u0443\u043a\u043d\u0435\u0440 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u044f \u2116 7 (\u0424\u0440\u0430\u043d\u0446 \u041a\u043e\u043d\u0432\u0438\u0447\u043d\u044b\u0439) - 1993, FLAC (tracks+.cue) lossless"
        self.assertEqual(collector.clean_body(body),
            'Anton Bruckner - Symphonie Nr. 7 / Symphony No. 7 / Антон Брукнер - Симфония № 7 - 1993, FLAC lossless')


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
        res = list(collector.iterate_parsers())
        pprint(res)
        self.assertTrue(res)
        self.assertTrue(all(r.id is not None for r in res))
        self.assertTrue(all(issubclass(r, base.BaseParser) for r in res))
