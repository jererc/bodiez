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

    def _collect(self, url, headless=True):
        config = Config(
            __file__,
            SHARED_STORE_PATH=os.path.join(WORK_PATH, 'bodiez'),
            GOOGLE_CREDS=None,
            FIRESTORE_COLLECTION='test',
            MIN_BODIES_HISTORY=10,
            HEADLESS=headless,
        )
        remove_path(config.SHARED_STORE_PATH)
        return module.Collector(config)._collect_bodies(module.URLItem(**url))

    def _test_collect(self, *args, **kwargs):
        res = self._collect(*args, **kwargs)
        self.assertTrue(res)
        self.assertTrue(all(isinstance(r, str) for r in res))
        self.assertTrue(len(set(res)) > len(res) * .9)


class NotifyTestCase(BaseTestCase):
    def _notify(self, url_item, bodies):
        config = Config(
            __file__,
            URLS=[],
            SHARED_STORE_PATH=os.path.join(WORK_PATH, 'bodiez'),
            GOOGLE_CREDS=None,
            FIRESTORE_COLLECTION='test',
            MIN_BODIES_HISTORY=10,
        )
        collector = module.Collector(config)
        collector._notify_new_bodies(url_item, bodies=bodies)

    def test_1(self):
        bodies = [
            "Lords of the Fallen: Deluxe Edition (v1.6.49 + 6 DLCs/Bonuses + Multiplayer, MUL...",
            "Slackers: Carts of Glory (v0.9975, MULTi12) [FitGirl Repack]",
            "Roboquest: Digital Deluxe Edition (v1.5.0-280/Endless Update + Bonus Content + W...",
            "The Black Grimoire: Cursebreaker (Build 16377283) [FitGirl Repack]",
            "My Dream Setup: Complete Edition (Build 16575801 + 4 DLCs, MULTi12) [FitGirl Rep...",
            "DON'T SCREAM (v1.0/Release, MULTi17) [FitGirl Repack]",
            "The Troop (Build 20241125 + US Forces DLC, MULTi10) [FitGirl Repack]",
            "Alaloth: Champions of The Four Kingdoms - Deluxe Edition (v1.0/Release + 4 DLCs/...",
            "Project Wingman: Frontline-59 Edition (v2.1.0.A.24.1202.9377 + DLC + Windows 7 F...",
            "Monster Hunter Stories (v1.1.0/Denuvoless + DLC + Bonus OST + Windows 7 Fix, MUL...",
            "METAL SLUG ATTACK RELOADED (v1029101748, MULTi12) [FitGirl Repack]",
            "Fruitbus: Fine Dining Edition (v1.0.4-24957 + Bonus Soundtrack, MULTi10) [FitGir...",
            "Shredders: 540INDY Edition (Glacier Update + 13 DLCs, MULTi10) [FitGirl Repack]",
            "Halluci-Sabbat of Koishi (v1.1.12 + Bonus Content, MULTi3) [FitGirl Repack, Sele...",
            "Automobilista 2 (v1.6.3.0.2752 + 20 DLCs, MULTi6) [FitGirl Repack]",
            "Skies above the Great War (MULTi25) [FitGirl Repack, Selective Download - from 8...",
            "Deathbound: Ultimate Edition (v1.1.8f1 + 4 DLCs/Bonuses, MULTi13) [FitGirl Repac...",
            "MXGP 24: The Official Game - Fox Holeshot Edition (+ 5 DLCs, MULTi11) [FitGirl R...",
            "MEGATON MUSASHI W: WIRED - Deluxe Edition (v3.1.4 + 39 DLCs, MULTi8) [FitGirl Re...",
            "BEYBLADE X XONE (v1.0.0 + Bypass Save Fixes, ENG/JAP) [FitGirl Repack]"
        ]
        url_item = module.URLItem(
            url='https://1337x.to/user/FitGirl/',
            id='FitGirl',
            cleaner=None,
        )
        self._notify(url_item, bodies=bodies)

    def test_2(self):
        bodies = [
            "Residential land - 501.87 m\u00b2, Albion, West, Rs 4,227,200",
            "Residential land - 613.56 m\u00b2, Albion, West, Rs 4,845,000",
            "Residential land - 556 m\u00b2, Albion, West, Rs 4,400,000",
            "Apartment - 2 Bedrooms - 70 m\u00b2, Flic en Flac, West, Rs 3,700,000",
            "Residential land - 414 m\u00b2, Albion, West, Rs 4,300,000",
            "Residential land - 468.51 m\u00b2, Albion, West, Rs 3,198,000",
            "House / Villa - 4 Bedrooms - 158 m\u00b2, Pointe aux Sables, West, Rs 3,800,000",
            "Residential land - 368.52 m\u00b2, Pointe aux Sables, West, Rs 2,900,000",
            "Apartment - 3 Bedrooms - 60 m\u00b2, Pointe aux Sables, West, Rs 950,000",
            "Residential land - 502.15 m\u00b2, Albion, West, Rs 4,227,200",
            "Residential land - 613.59 m\u00b2, Albion, West, Rs 4,845,000",
            "Apartment - 1 Bedroom - 45 m\u00b2, Flic en Flac, West, Rs 4,500,000",
            "Residential land - 759.83 m\u00b2, Pointe aux Sables, West, Rs 4,700,000",
            "Residential land - 575 m\u00b2, Albion, West, Rs 4,500,000",
            "Residential land - 367 m\u00b2, Pointe aux Sables, West, Rs 3,200,000",
            "Residential land - 760 m\u00b2, Albion, West, Rs 5,000,000"
        ]
        url_item = module.URLItem(
            url='https://www.lexpressproperty.com/en/buy-mauritius/all/west/?price_max=5000000&currency=MUR&filters%5Binterior_unit%5D%5Beq%5D=m2&filters%5Bland_unit%5D%5Beq%5D=m2',
            id='land-for-sale',
            cleaner=lambda x: x.replace('Residential land - ', '').strip(),
            max_bodies_per_notif=3,
        )
        self._notify(url_item, bodies=bodies)

    def test_3(self):
        bodies = [
            "Residential land - 760 m\u00b2\rAlbion, West\rRs 5,000,000",
            "Apartment - 2 Bedrooms - 65 m\u00b2\rFlic en Flac, West\rRs 4,700,000",
            "Residential land - 501.87 m\u00b2\rAlbion, West\rRs 4,227,200",
            "Residential land - 613.56 m\u00b2\rAlbion, West\rRs 4,845,000",
            "Residential land - 556 m\u00b2\rAlbion, West\rRs 4,400,000",
            "Apartment - 2 Bedrooms - 70 m\u00b2\rFlic en Flac, West\rRs 3,700,000",
            "Residential land - 414 m\u00b2\rAlbion, West\rRs 4,300,000",
            "Residential land - 468.51 m\u00b2\rAlbion, West\rRs 3,198,000",
            "House / Villa - 4 Bedrooms - 158 m\u00b2\rPointe aux Sables, West\rRs 3,800,000",
            "Residential land - 368.52 m\u00b2\rPointe aux Sables, West\rRs 2,900,000",
            "Apartment - 3 Bedrooms - 60 m\u00b2\rPointe aux Sables, West\rRs 950,000",
            "Residential land - 502.15 m\u00b2\rAlbion, West\rRs 4,227,200",
            "Residential land - 613.59 m\u00b2\rAlbion, West\rRs 4,845,000",
            "Apartment - 1 Bedroom - 45 m\u00b2\rFlic en Flac, West\rRs 4,500,000",
            "Residential land - 759.83 m\u00b2\rPointe aux Sables, West\rRs 4,700,000",
            "Residential land - 575 m\u00b2\rAlbion, West\rRs 4,500,000"
        ]
        url_item = module.URLItem(
            url='https://www.lexpressproperty.com/en/buy-mauritius/all/west/?price_max=5000000&currency=MUR&filters%5Binterior_unit%5D%5Beq%5D=m2&filters%5Bland_unit%5D%5Beq%5D=m2',
            id='land-for-sale',
        )
        self._notify(url_item, bodies=bodies)


class GenericTestCase(BaseTestCase):
    def test_1337x(self):
        self._test_collect(
            {
                'url': 'https://1337x.to/user/FitGirl/',
                'xpath': '//table/tbody/tr/td[1]/a[2]',
            },
            headless=False,
        )

    def test_1337x_sub(self):
        self._test_collect(
            {
                'url': 'https://1337x.to/user/FitGirl/',
                'parent_xpath': '//table/tbody/tr',
                'child_xpaths': [
                    './/td[1]/a[2]',
                ],
            },
            headless=False,
        )

    def test_nvidia(self):
        self._test_collect(
            {
                'url': 'https://www.nvidia.com/en-us/geforce/news/',
                'xpath': '//div[contains(@class, "article-title-text")]/a',
            },
            headless=False,
        )

    def test_nvidia_sub(self):
        self._test_collect(
            {
                'url': 'https://www.nvidia.com/en-us/geforce/news/',
                'parent_xpath': '//div[contains(@class, "article-title-text")]',
                'child_xpaths': [
                    './/a',
                ],
            },
            headless=False,
        )

    def test_lexpress(self):
        self._test_collect(
            {
                'url': 'https://www.lexpressproperty.com/en/buy-mauritius/all/west/?price_max=5000000&currency=MUR&filters%5Binterior_unit%5D%5Beq%5D=m2&filters%5Bland_unit%5D%5Beq%5D=m2',
                'parent_xpath': '//div[contains(@class, "card-row")]',
                'child_xpaths': [
                    './/div[contains(@class, "title-holder")]/h2',
                    './/address',
                    './/div[contains(@class, "card-foot-price")]/strong/a',
                ],
                'multi_element_delimiter': '\r',
            },
            headless=False,
        )

    def test_rutracker(self):
        self._test_collect(
            {
                'url': 'https://rutracker.org/forum/tracker.php?f=557',
                'xpath': '//div[contains(@class, "t-title")]/a',
            },
            headless=False,
        )


class TimeoutTestCase(BaseTestCase):
    def test_timeout(self):
        self.assertRaises(Exception, self._collect,
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


class GeforceDriverVersionTestCase(BaseTestCase):
    def test_1(self):
        self._test_collect(
            {
                'url': 'geforce-driver-version',
            },
            headless=True,
        )


class WorkflowTestCase(BaseTestCase):
    def test_1(self):
        config = Config(
            __file__,
            URLS=[
                {
                    'url': 'https://1337x.to/user/FitGirl/',
                    'xpath': '//table/tbody/tr/td[1]/a[2]',
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
        self.assertEqual(len(mock_send.call_args_list), 4)

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
