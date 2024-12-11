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


class FirestoreTestCase(unittest.TestCase):
    def setUp(self):
        remove_path(WORK_DIR)
        makedirs(WORK_DIR)
        self.fs = store.Firestore(Config(
            __file__,
            GOOGLE_CREDS=GOOGLE_CREDS,
            FIRESTORE_COLLECTION='test',
            HEADLESS=True,
        ))
        self.url = 'https://1337x.to/user/FitGirl/'
        self.bodies = [f'body {i}' for i in range(1, 51)]
        self.fs.col.document(self.fs._get_doc_id(self.url)).delete()

    def test_workflow(self):
        doc = self.fs.get(self.url)
        pprint(doc)
        self.assertEqual(doc.url, self.url)
        self.assertEqual(doc.bodies, [])
        self.assertEqual(doc.updated_ts, 0)

        self.fs.set(self.url, bodies=[])
        doc = self.fs.get(self.url)
        pprint(doc)
        self.assertEqual(doc.url, self.url)
        self.assertEqual(doc.bodies, [])
        self.assertTrue(doc.updated_ts > 0)

        bodies = self.bodies[5:15]
        self.fs.set(self.url, bodies=bodies)
        doc = self.fs.get(self.url)
        pprint(doc)
        self.assertEqual(doc.url, self.url)
        self.assertEqual(doc.bodies, bodies)
        self.assertTrue(doc.updated_ts > 0)

        bodies = self.bodies[3:13]
        self.fs.set(self.url, bodies=bodies)
        doc = self.fs.get(self.url)
        pprint(doc)
        self.assertEqual(doc.url, self.url)
        self.assertEqual(doc.bodies, bodies)
        self.assertTrue(doc.updated_ts > 0)


class SharedStoreTestCase(unittest.TestCase):
    def setUp(self):
        remove_path(WORK_DIR)
        makedirs(WORK_DIR)
        self.sl = store.SharedStore(Config(
            __file__,
            SHARED_STORE_DIR=os.path.join(WORK_DIR, 'store'),
            HEADLESS=True,
        ))
        self.url = 'https://1337x.to/user/FitGirl/'
        self.url2 = 'https://1337x.to/user/DODI/'
        self.bodies = [f'body {i}' for i in range(1, 51)]

    def test_workflow(self):
        doc = self.sl.get(self.url2)
        pprint(doc)
        self.sl.set(self.url2, bodies=['1', '2'])

        doc = self.sl.get(self.url)
        pprint(doc)
        self.assertEqual(doc.url, self.url)
        self.assertEqual(doc.bodies, [])
        self.assertEqual(doc.updated_ts, 0)

        time.sleep(.01)
        self.sl.set(self.url, bodies=[])
        doc = self.sl.get(self.url)
        pprint(doc)
        self.assertEqual(doc.bodies, [])

        set_bodies = self.bodies[6:16]
        time.sleep(.01)
        self.sl.set(self.url, bodies=set_bodies)
        doc = self.sl.get(self.url)
        pprint(doc)
        self.assertEqual(doc.bodies, set_bodies)

        set_bodies = self.bodies[3:13]
        time.sleep(.01)
        self.sl.set(self.url, bodies=set_bodies)
        doc = self.sl.get(self.url)
        pprint(doc)
        self.assertEqual(doc.bodies, set_bodies)

        doc = self.sl.get(self.url2)
        pprint(doc)
        self.assertEqual(doc.url, self.url2)
        self.assertEqual(doc.bodies, ['1', '2'])
        self.assertTrue(doc.updated_ts > 0)
