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


GOOGLE_CREDS = os.path.join(WORK_DIR, 'google_creds.json')
# GOOGLE_CREDS = os.path.join(os.path.expanduser('~'), 'gcs-bodiez.json')

module.logger.setLevel(logging.DEBUG)


def remove_path(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)


def makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)


class FirestoreTestCase(unittest.TestCase):
    def setUp(self):
        remove_path(WORK_DIR)
        makedirs(WORK_DIR)
        self.fs = store.Firestore(Config(
            __file__,
            FIRESTORE_COLLECTION='test',
            HEADLESS=True,
        ))
        self.url = 'https://1337x.to/user/FitGirl/'
        self.titles = [f'body {i}' for i in range(1, 51)]
        self.fs.col.document(self.fs._get_doc_id(self.url)).delete()

    def test_workflow(self):
        doc = self.fs.get(self.url)
        pprint(doc)
        self.assertEqual(doc.url, self.url)
        self.assertEqual(doc.titles, [])
        self.assertEqual(doc.updated_ts, 0)

        self.fs.set(self.url, titles=[])
        doc = self.fs.get(self.url)
        pprint(doc)
        self.assertEqual(doc.url, self.url)
        self.assertEqual(doc.titles, [])
        self.assertTrue(doc.updated_ts > 0)

        titles = self.titles[5:15]
        self.fs.set(self.url, titles=titles)
        doc = self.fs.get(self.url)
        pprint(doc)
        self.assertEqual(doc.url, self.url)
        self.assertEqual(doc.titles, titles)
        self.assertTrue(doc.updated_ts > 0)

        titles = self.titles[3:13]
        self.fs.set(self.url, titles=titles)
        doc = self.fs.get(self.url)
        pprint(doc)
        self.assertEqual(doc.url, self.url)
        self.assertEqual(doc.titles, titles)
        self.assertTrue(doc.updated_ts > 0)


class CloudSyncStoreTestCase(unittest.TestCase):
    def setUp(self):
        remove_path(WORK_DIR)
        makedirs(WORK_DIR)
        self.sl = store.CloudSyncStore(Config(
            __file__,
            STORE_DIR=os.path.join(WORK_DIR, 'store'),
            HEADLESS=True,
        ))
        self.url = 'https://1337x.to/user/FitGirl/'
        self.url2 = 'https://1337x.to/user/DODI/'
        self.titles = [f'body {i}' for i in range(1, 51)]

    def test_workflow(self):
        doc = self.sl.get(self.url2)
        pprint(doc)
        self.sl.set(self.url2, titles=['1', '2'])

        doc = self.sl.get(self.url)
        pprint(doc)
        self.assertEqual(doc.url, self.url)
        self.assertEqual(doc.titles, [])
        self.assertEqual(doc.updated_ts, 0)

        time.sleep(.01)
        self.sl.set(self.url, titles=[])
        doc = self.sl.get(self.url)
        pprint(doc)
        self.assertEqual(doc.titles, [])

        set_titles = self.titles[6:16]
        time.sleep(.01)
        self.sl.set(self.url, titles=set_titles)
        doc = self.sl.get(self.url)
        pprint(doc)
        self.assertEqual(doc.titles, set_titles)

        set_titles = self.titles[3:13]
        time.sleep(.01)
        self.sl.set(self.url, titles=set_titles)
        doc = self.sl.get(self.url)
        pprint(doc)
        self.assertEqual(doc.titles, set_titles)

        doc = self.sl.get(self.url2)
        pprint(doc)
        self.assertEqual(doc.url, self.url2)
        self.assertEqual(doc.titles, ['1', '2'])
        self.assertTrue(doc.updated_ts > 0)
