import logging
import os
from pprint import pprint
import shutil
import unittest
from unittest.mock import patch

from svcutils.service import Config

import bodiez as module
WORK_PATH = os.path.join(os.path.expanduser('~'), '_tests', 'bodiez')
module.WORK_PATH = WORK_PATH
module.logger.setLevel(logging.DEBUG)
module.logger.handlers.clear()
from bodiez import collector as module, parsers
from bodiez.firestore import FireStore


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
        fs = FireStore(config)
        print(f'deleting all documents in firestore collection '
            f'{fs.collection_name}...')
        for doc in fs.col.list_documents():
            doc.delete()

    def _collect(self, urls, headless=True, reset_storage=True):
        config = Config(
            __file__,
            HEADLESS=headless,
            URLS=urls,
            GOOGLE_CREDS=GOOGLE_CREDS,
            FIRESTORE_COLLECTION='test',
        )
        if reset_storage:
            self._reset_storage(config)
        return module.collect(config)


class X1337xTestCase(BaseTestCase):
    def test_no_result(self):
        self._collect([
            'https://1337x.to/search/sfsfsfsdfsd/1/',
        ])

    def test_invalid_title(self):
        with patch.object(parsers.X1337xParser, '_get_title') as mock__get_title:
            mock__get_title.return_value = ''
            self._collect([
                ('https://1337x.to/cat/Movies/1/', 'movies'),
            ])

    def test_ok(self):
        self._collect([
            'https://1337x.to/user/FitGirl/',
            # 'https://1337x.to/user/DODI/',
            # 'https://1337x.to/sort-search/battlefield%20repack/time/desc/1/',
            # ('https://1337x.to/cat/Movies/1/', 'movies'),
        ])


class RutrackerTestCase(BaseTestCase):
    def test_ok(self):
        self._collect([
            'https://rutracker.org/forum/tracker.php?f=557',
            ],
            headless=False,
        )


class NvidiaGeforceTestCase(BaseTestCase):
    def test_ok(self):
        self._collect([
            ('https://www.nvidia.com/en-us/geforce/news/', 'geforce news'),
            ],
            # headless=False,
        )


class CollectTestCase(BaseTestCase):
    def test_all(self):
        self._collect([
            ('https://1337x.to/user/FitGirl/', 'FitGirl'),
            ('https://rutracker.org/forum/tracker.php?f=557', 'rutracker classical'),
            ('https://www.nvidia.com/en-us/geforce/news/', 'geforce news'),
            ],
            # headless=False,
        )

    def test_new(self):
        urls = [
            'https://1337x.to/user/FitGirl/',
        ]
        call_args_lists = []
        for i in range(2):
            with patch.object(module.Notifier, 'send') as mock_send:
                self._collect(urls, reset_storage=i == 0)
            pprint(mock_send.call_args_list)
            call_args_lists.append(mock_send.call_args_list)
        self.assertTrue(len(call_args_lists[0]), module.MAX_NOTIF_PER_URL)
        self.assertFalse(call_args_lists[1])
