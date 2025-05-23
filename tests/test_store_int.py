import json
import logging
import os
from pprint import pprint
import shutil
import time
import unittest

from svcutils.service import Config

import bodiez as module
WORK_DIR = os.path.join(os.path.expanduser('~'), '_tests', 'bodiez')
module.WORK_DIR = WORK_DIR
module.logger.setLevel(logging.DEBUG)
module.logger.handlers.clear()
from bodiez import store


module.logger.setLevel(logging.DEBUG)


def remove_path(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)


class CloudSyncStoreTestCase(unittest.TestCase):
    def setUp(self):
        remove_path(WORK_DIR)
        os.makedirs(WORK_DIR, exist_ok=True)
        self.store = store.CloudSyncStore(Config(
            __file__,
            STORE_DIR=os.path.join(WORK_DIR, 'store'),
            HEADLESS=True,
        ))
        self.url = 'https://1337x.to/user/FitGirl/'
        self.url2 = 'https://1337x.to/user/DODI/'
        self.titles = [f'body {i}' for i in range(1, 51)]

    def _create_file(self, url, titles, hostname):
        file = os.path.join(self.store.base_dir,
            f'{self.store._get_doc_id(url)}-{hostname}.json')
        data = {
            'url': url,
            'titles': titles,
            'updated_ts': time.time(),
            'ref': file,
        }
        with open(file, 'w', encoding='utf-8') as fd:
            json.dump(data, fd, sort_keys=True, indent=4)

    def test_workflow(self):
        doc = self.store.get(self.url2)
        pprint(doc)
        self.store.set(self.url2, titles=['1', '2'])

        doc = self.store.get(self.url)
        pprint(doc)
        self.assertEqual(doc.url, self.url)
        self.assertEqual(doc.titles, [])
        self.assertEqual(doc.updated_ts, 0)

        time.sleep(.01)
        self.store.set(self.url, titles=[])
        doc = self.store.get(self.url)
        pprint(doc)
        self.assertEqual(doc.titles, [])

        set_titles = self.titles[6:16]
        time.sleep(.01)
        self.store.set(self.url, titles=set_titles)
        doc = self.store.get(self.url)
        pprint(doc)
        self.assertEqual(doc.titles, set_titles)

        set_titles = self.titles[3:13]
        time.sleep(.01)
        self.store.set(self.url, titles=set_titles)
        doc = self.store.get(self.url)
        pprint(doc)
        self.assertEqual(doc.titles, set_titles)

        doc = self.store.get(self.url2)
        pprint(doc)
        self.assertEqual(doc.url, self.url2)
        self.assertEqual(doc.titles, ['1', '2'])
        self.assertTrue(doc.updated_ts > 0)

        doc = self.store.get(self.url)
        other_host_titles = ['new_title'] + doc.titles
        self._create_file(self.url, titles=other_host_titles,
            hostname='another_host')
        doc = self.store.get(self.url)
        pprint(doc)
        self.assertEqual(doc.titles, other_host_titles)
