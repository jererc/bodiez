import logging
import os
from pprint import pprint
import shutil
from threading import Thread
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
        self.titles = [
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
        # Get documents
        self.results = []
        def get():
            self.results.append(self.fs.get(self.url))
        ths = [Thread(target=get) for i in range(3)]
        for th in ths:
            th.start()
        for th in ths:
            th.join()
        pprint(self.results)
        self.assertEqual(len({r['ref'].id for r in self.results}), 1)

        # Handle new titles
        res = self.results[0]
        pprint(res)
        doc_ref = res['ref']
        titles = self.titles[3:13]
        new_titles = [r for r in titles if r not in res['data']['titles']]
        pprint(new_titles)
        self.assertEqual(new_titles, titles)

        # Update documents
        self.results = []
        def update(doc_ref, titles):
            self.results.append(self.fs.update_ref(doc_ref, titles))
        ths = [Thread(target=update, args=(doc_ref, titles,)) for i in range(3)]
        for th in ths:
            th.start()
        for th in ths:
            th.join()
        pprint(self.results)

        res = self.fs.get(self.url)
        pprint(res)
        self.assertEqual(res['data']['titles'], titles)
        doc_ref = res['ref']

        titles = self.titles[:10]
        self.results = []
        ths = [Thread(target=update, args=(doc_ref, titles,)) for i in range(3)]
        for th in ths:
            th.start()
        for th in ths:
            th.join()
        pprint(self.results)

        res = self.fs.get(self.url)
        pprint(res)
        self.assertEqual(res['data']['titles'], titles)
