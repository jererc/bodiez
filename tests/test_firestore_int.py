import logging
import os
from pprint import pprint
import shutil
import unittest

from svcutils.service import Config

import bodiez as module
WORK_PATH = os.path.join(os.path.expanduser('~'), '_tests', 'bodiez')
module.WORK_PATH = WORK_PATH
module.logger.setLevel(logging.DEBUG)
module.logger.handlers.clear()
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


class FireStoreTestCase(unittest.TestCase):
    def setUp(self):
        remove_path(WORK_PATH)
        makedirs(WORK_PATH)
        self.fs = FireStore(Config(
            __file__,
            HEADLESS=True,
            GOOGLE_CREDS=GOOGLE_CREDS,
            FIRESTORE_COLLECTION='test',
        ))
        self.url = 'https://1337x.to/user/FitGirl/'
        self.bodies = [
            "Expeditions: Rome (v1.6.0.741.23995 + Death or Glory DLC + Bonus OST, MULTi8) [F...",
            "Valkyrie of Phantasm (v1.04, MULTi3) [FitGirl Repack]",
            "MechWarrior 5: Clans - Digital Collectors Edition (v1.0.80 + 2 DLCs, MULTi5) [Fi...1",
            "Paper Ghost Stories: Third Eye Open (v1.0.4 + Bonus Soundtrack, MULTi4) [FitGirl...",
            "Incantation (v1.0.0.2, MULTi6) [FitGirl Repack]",
            "Homeworld 3 (v1.3-CL364034 + 8 DLCs/Bonuses, MULTi13) [FitGirl Repack, Selective...",
            "Luma Island (v1.19219 + Multiplayer, MULTi10) [FitGirl Repack]",
            "Massacre At The Mirage (+ Windows 7 Fix) [FitGirl Repack]",
            "CORPUS EDAX (Build 16101849) [FitGirl Repack]",
            "Albatroz (+ Windows 7 Fix, MULTi12) [FitGirl Repack, Selective Download - from 1...",
            "AWAKEN: Astral Blade - Deluxe Edition (v202411181541 + 3 DLCs/Bonuses, MULTi12) ...",
            "Mercury Abbey (ENG/CHS) [FitGirl Repack]",
            "CarX Street: Deluxe Edition (v1.2.1 + 3 DLCs, MULTi7) [FitGirl Repack]",
            "\u00c9t\u00e9 (v1.0.2 + Bonus Soundtracks, ENG/FRA) [FitGirl Repack]",
            "Jujutsu Kaisen: Cursed Clash - Ultimate Edition (v1.4.0 + 7 DLCs/Bonuses + Windo...",
            "Codex Lost (v1.0.3 + Windows 7 Fix) [FitGirl Repack]",
            "Apocalypse Party (Build 16145511 + DLC, MULTi6) [FitGirl Repack]",
            "Pure Rock Crawling (v1.0/Release + Windows 7 Fix) [FitGirl Repack]",
            "Subverse (v1.0/Release) [FitGirl Repack]4",
            "Victoria 3: Grand Edition (v1.8.0/Masala Chai + 11 DLCs/Bonuses + Windows 7 Fix,..."
        ]
        self.fs.col.document(self.fs._get_doc_id(self.url)).delete()

    def test_workflow(self):
        doc = self.fs.get(self.url)
        pprint(doc)
        self.assertEqual(doc.url, self.url)
        self.assertEqual(doc.bodies, [])
        self.assertEqual(doc.updated_ts, 0)

        self.fs.set(self.url, bodies=None)
        doc = self.fs.get(self.url)
        pprint(doc)
        self.assertEqual(doc.url, self.url)
        self.assertEqual(doc.bodies, [])
        self.assertTrue(doc.updated_ts > 0)

        bodies = self.bodies[5:15]
        self.fs.set(self.url, bodies=bodies)
        doc = self.fs.get(self.url)
        self.assertEqual(doc.url, self.url)
        self.assertEqual(doc.bodies, bodies)
        self.assertTrue(doc.updated_ts > 0)

        bodies = self.bodies[3:13]
        self.fs.set(self.url, bodies=bodies)
        doc = self.fs.get(self.url)
        self.assertEqual(doc.url, self.url)
        self.assertEqual(doc.bodies, bodies)
        self.assertTrue(doc.updated_ts > 0)
