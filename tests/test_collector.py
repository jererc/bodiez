import logging
import os
from pprint import pprint
import shutil
import time
import unittest
from unittest.mock import patch

import bodiez as module
WORK_PATH = os.path.join(os.path.expanduser('~'), '_tests', 'bodiez')
module.WORK_PATH = WORK_PATH
module.logger.setLevel(logging.DEBUG)
module.logger.handlers.clear()
from bodiez import collector, storage
from bodiez.parsers import base


def remove_path(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)


def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


class StorageTestCase(unittest.TestCase):
    def setUp(self):
        remove_path(WORK_PATH)
        makedirs(WORK_PATH)
        self.base_path = os.path.join(WORK_PATH, 'bodies')

    def _gen_titles(self, keys):
        return {str(k): 0 for k in keys}

    def test_1(self):
        url1 = 'https://1337x.to/user/1/'
        url2 = 'https://1337x.to/user/2/'

        obj = storage.SharedLocalStore(base_path=self.base_path)
        self.assertTrue(obj._get_dst_path(url1) != obj._get_dst_path(url2))

        all_titles = self._gen_titles(range(1, 6))
        new_titles = obj.get_new_titles(url1, all_titles)
        self.assertEqual(new_titles, all_titles)
        obj.save(url1, all_titles, new_titles)

        all_titles = self._gen_titles(range(3, 8))
        new_titles = obj.get_new_titles(url1, all_titles)
        self.assertEqual(new_titles, self._gen_titles(range(6, 8)))
        obj.save(url1, all_titles, new_titles)

        obj = storage.SharedLocalStore(base_path=self.base_path)
        all_titles = self._gen_titles(range(7, 11))
        new_titles = obj.get_new_titles(url1, all_titles)
        self.assertEqual(new_titles, self._gen_titles(range(8, 11)))
        obj.save(url1, all_titles, new_titles)

        url1_items = obj._load_titles(url1)
        self.assertTrue(url1_items)

        all_titles = self._gen_titles(range(11, 21))
        new_titles = obj.get_new_titles(url2, all_titles)
        self.assertEqual(new_titles, all_titles)
        obj.save(url2, all_titles, new_titles)

        all_titles = self._gen_titles(range(13, 24))
        new_titles = obj.get_new_titles(url2, all_titles)
        self.assertEqual(new_titles, self._gen_titles(range(21, 24)))
        obj.save(url2, all_titles, new_titles)

        url1_items2 = obj._load_titles(url1)
        self.assertEqual(url1_items2, url1_items)

        with patch.object(storage, 'get_file_mtime') as mock_get_file_mtime:
            mock_get_file_mtime.return_value = time.time() - storage.STORAGE_RETENTION_DELTA - 1
            obj.cleanup({url2})
        self.assertFalse(obj._load_titles(url1))
        self.assertTrue(obj._load_titles(url2))


class CleanTitleTestCase(unittest.TestCase):
    def test_1(self):
        title = 'L.A. Noire: The Complete Edition (v2675.1 + All DLCs, MULTi6) [FitGirl Repack]'
        self.assertEqual(collector.clean_title(title), 'L.A. Noire: The Complete Edition')

    def test_2(self):
        title = 'L.A. Noire: The Complete Edition (v2675.1 + All DLCs, MULTi6) [FitGirl...'
        self.assertEqual(collector.clean_title(title), 'L.A. Noire: The Complete Edition')

    def test_3(self):
        title = 'L.A. Noire: The Complete Edition (v2675.1 + All DLCs, ...'
        self.assertEqual(collector.clean_title(title), 'L.A. Noire: The Complete Edition')

    def test_4(self):
        title = 'L.A. Noire (The Complete Edition) (v2675.1 + All DLCs, ...'
        self.assertEqual(collector.clean_title(title), 'L.A. Noire')

    def test_5(self):
        title = 'L.A. Noire [X] (v2675.1 + All DLCs, MULTi6) [FitGirl Repack]'
        self.assertEqual(collector.clean_title(title), 'L.A. Noire')

    def test_6(self):
        title = '[X] L.A. Noire (v2675.1 + All DLCs, MULTi6) [FitGirl Repack]'
        self.assertEqual(collector.clean_title(title), 'L.A. Noire')


class URLItemTestCase(unittest.TestCase):
    def test_1(self):
        urls = [
            'https://1337x.to/user/FitGirl/',
            ('https://1337x.to/sort-search/monster%20hunter%20repack/time/desc/1/', 'monster hunter'),
            'https://rutracker.org/forum/tracker.php?f=557',
        ]
        res = [collector.URLItem(r) for r in urls]
        pprint(res)
        self.assertTrue(all(bool(r.id) for r in res))
        self.assertTrue(all(bool(r.url) for r in res))


class ParsersTestCase(unittest.TestCase):
    def test_1(self):
        res = list(base.iterate_parsers())
        pprint(res)
        self.assertTrue(res)
        self.assertTrue(all(r.id is not None for r in res))
        self.assertTrue(all(issubclass(r, base.BaseParser) for r in res))
