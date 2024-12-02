import logging
import os
from pprint import pprint
import shutil
import time
import unittest
from unittest.mock import patch

from svcutils.service import Config

import bodiez as module
WORK_PATH = os.path.join(os.path.expanduser('~'), '_tests', 'bodiez')
module.WORK_PATH = WORK_PATH
module.logger.setLevel(logging.DEBUG)
module.logger.handlers.clear()
from bodiez import collector as module
from bodiez.store import Firestore


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
        fs = Firestore(config)
        print(f'deleting all documents in firestore collection '
            f'{config.FIRESTORE_COLLECTION}...')
        for doc in fs.col.list_documents():
            doc.delete()
        remove_path(config.SHARED_STORE_PATH)

    def _collect(self, urls, headless=True, reset_storage=True):
        config = Config(
            __file__,
            URLS=[r if isinstance(r, dict) else {'url': r}
                for r in urls],
            SHARED_STORE_PATH=os.path.join(WORK_PATH, 'bodiez'),
            GOOGLE_CREDS=GOOGLE_CREDS,
            FIRESTORE_COLLECTION='test',
            MIN_BODIES_HISTORY=10,
            HEADLESS=headless,
        )
        if reset_storage:
            self._reset_storage(config)
        return module.collect(config)


class X1337xTestCase(BaseTestCase):
    def test_no_result(self):
        self._collect([
                {
                    'url': 'https://1337x.to/search/asdasdasdasd/1/',
                    'id': 'epic id',
                    'allow_no_results': True,
                },
            ],
            headless=False,
        )

    def test_ok(self):
        self._collect([
            'https://1337x.to/user/FitGirl/',
            # 'https://1337x.to/user/DODI/',
            'https://1337x.to/sort-search/battlefield%20repack/time/desc/1/',
            'https://1337x.to/cat/Movies/1/',
            ],
            # headless=False,
        )


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
            'https://www.nvidia.com/en-us/geforce/news/',
            ],
            headless=False,
        )


class LexpresspropertyTestCase(BaseTestCase):
    def test_no_result(self):
        self._collect([
            'https://www.lexpressproperty.com/en/buy-mauritius/all/la_gaulette-la_preneuse/?price_max=5000000&currency=MUR&filters%5Binterior_unit%5D%5Beq%5D=m2&filters%5Bland_unit%5D%5Beq%5D=m2',
            ],
            # headless=False,
        )

    def test_ok(self):
        self._collect([
            'https://www.lexpressproperty.com/en/buy-mauritius/all/west/?price_max=5000000&currency=MUR&filters%5Binterior_unit%5D%5Beq%5D=m2&filters%5Bland_unit%5D%5Beq%5D=m2',
            ],
            # headless=False,
        )


class CollectTestCase(BaseTestCase):
    def test_all(self):
        self._collect([
            'https://1337x.to/user/FitGirl/',
            # 'https://rutracker.org/forum/tracker.php?f=557',
            'https://www.nvidia.com/en-us/geforce/news/',
            'https://www.lexpressproperty.com/en/buy-mauritius/all/west/?price_max=5000000&currency=MUR&filters%5Binterior_unit%5D%5Beq%5D=m2&filters%5Bland_unit%5D%5Beq%5D=m2',
            ],
            # headless=False,
        )


class WorkflowTestCase(BaseTestCase):
    def test_1(self):
        config = Config(
            __file__,
            URLS=[
                {
                    'url': 'https://1337x.to/user/FitGirl/',
                    'update_delta': 0,
                },
            ],
            SHARED_STORE_PATH=os.path.join(WORK_PATH, 'bodiez'),
            GOOGLE_CREDS=GOOGLE_CREDS,
            FIRESTORE_COLLECTION='test',
            MIN_BODIES_HISTORY=10,
        )
        self._reset_storage(config)
        collector = module.Collector(config)

        def run():
            time.sleep(.01)
            collector.run()

        doc = collector.store.get(config.URLS[0]['url'])
        pprint(doc)
        self.assertFalse(doc.bodies)

        with patch.object(module.Notifier, 'send') as mock_send:
            run()
        pprint(mock_send.call_args_list)
        self.assertEqual(len(mock_send.call_args_list),
            module.MAX_NOTIF_PER_URL)

        doc = collector.store.get(config.URLS[0]['url'])
        pprint(doc)
        self.assertTrue(doc.bodies)

        with patch.object(module.Notifier, 'send') as mock_send:
            run()
        pprint(mock_send.call_args_list)
        self.assertFalse(mock_send.call_args_list)

        new_bodies = [f'body {i}' for i in range(2)]
        with patch.object(module.Notifier, 'send') as mock_send, \
                patch.object(collector,
                    '_collect_bodies') as mock__collect_bodies:
            mock__collect_bodies.return_value = (new_bodies
                + doc.bodies[:-len(new_bodies)])
            run()
        pprint(mock_send.call_args_list)
        prev_doc_bodies = doc.bodies
        doc = collector.store.get(config.URLS[0]['url'])
        pprint(doc)
        self.assertEqual(doc.bodies, new_bodies + prev_doc_bodies)
