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

    def test_4(self):
        bodies = [
            "\u0427\u0430\u0439\u043a\u043e\u0432\u0441\u043a\u0438\u0439 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u044f \u21166, \u0424\u0440\u0430\u043d\u0447\u0435\u0441\u043a\u0430 \u0434\u0430 \u0420\u0438\u043c\u0438\u043d\u0438 (\u041e\u0440\u043a\u0435\u0441\u0442\u0440 \"\u041d\u043e\u0432\u0430\u044f \u0420\u043e\u0441\u0441\u0438\u044f\", \u0413\u043e\u0440\u0435\u043d\u0448\u0442\u0435\u0439\u043d) - 1996, Gold CD, FLAC (image+.cue) lossless",
            "Anton Bruckner - Symphonie Nr. 7 / Symphony No. 7 (Gewandhausorchester Leipzig - Franz Konwitschny) / \u0410\u043d\u0442\u043e\u043d \u0411\u0440\u0443\u043a\u043d\u0435\u0440 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u044f \u2116 7 (\u0424\u0440\u0430\u043d\u0446 \u041a\u043e\u043d\u0432\u0438\u0447\u043d\u044b\u0439) - 1993, FLAC (tracks+.cue) lossless",
            "Smetana - Ma vlast (Czech Philharmonic, Semyon Bychkov / \u0421\u0435\u043c\u0435\u043d \u0411\u044b\u0447\u043a\u043e\u0432) - 2024, FLAC (image+.cue) lossless",
            "Anton Bruckner - Symphonie Nr. 7 / Symphony No. 7 \u00b7 Franz Schubert - Symphonie Nr. 9 \u00bbGrosse C-Dur\u00ab / Symphony No. 9 (Prague Symphony Orchestra - Gaetano Delogu) - 1996, FLAC (tracks+.cue) lossless",
            "Anton Bruckner - Symphonie Nr. 6 / Symphony No. 6 (Gewandhausorchester Leipzig - Heinz Bongartz) / \u0410\u043d\u0442\u043e\u043d \u0411\u0440\u0443\u043a\u043d\u0435\u0440 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u044f \u2116 6 (\u0425\u0430\u0439\u043d\u0446 \u0411\u043e\u043d\u0433\u0430\u0440\u0442\u0446) - 1996, FLAC (tracks+.cue) lossless",
            "\u0410\u043b\u044c\u0444\u0440\u0435\u0434 \u0428\u043d\u0438\u0442\u043a\u0435 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u0438 \u2116\u2116 1 \u00b7 2 \u00b7 3 \u00b7 4 (\u0413\u0435\u043d\u043d\u0430\u0434\u0438\u0439 \u0420\u043e\u0436\u0434\u0435\u0441\u0442\u0432\u0435\u043d\u0441\u043a\u0438\u0439) / Alfred Schnittke - Symphonies Nos. 1 \u00b7 2 \u00b7 3 \u00b7 4 (Gennady Rozhdestvensky) - 2006, FLAC (tracks+.cue) lossless",
            "Saxton - Scenes from the Epic of Gilgamesh; The Resurrection of the Soldiers (English Symphony Orchestra, English String Orchestra, Kenneth Woods) - 2024, FLAC (image+.cue) lossless",
            "Anton Bruckner - Symphonie Nr. 6 / Symphony No. 6 (Bohuslav Martinu Philharmonic - Georg Tintner) / \u0410\u043d\u0442\u043e\u043d \u0411\u0440\u0443\u043a\u043d\u0435\u0440 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u044f \u2116 6 (\u0413\u0435\u043e\u0440\u0433 \u0422\u0438\u043d\u0442\u043d\u0435\u0440) - 1994, FLAC (tracks+.cue) lossless",
            "Antal Dorati conducts: Kodaly - \"Hary Janos\" Suite, Dances of Galanta, Marosszek Dances \u2022 Bartok - Hungarian Sketches, Roumanian Folk Dances (Minneapolis Symphony Orchestra, Philharmonia Hungarica, Antal Dorati) [Mercury Living Presence\u200e] - 1990, APE (image+.cue) lossl",
            "Segerstam - Thoughts 1989; Thoughts 1990; Monumental Thoughts 'Martti Talvela In Memoriam' (The Kontra Quartet, Danish National Radio Symphony Orchestra, Leif Segerstam) - 1992, FLAC (image+.cue) lossless",
            "Anton Bruckner - Symphonie Nr. 6 / Symphony No. 6 (Cincinnati Symphony Orchestra - Jesus Lopez-Cobos) / \u0410\u043d\u0442\u043e\u043d \u0411\u0440\u0443\u043a\u043d\u0435\u0440 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u044f \u2116 6 (\u0425\u0435\u0441\u0443\u0441 \u041b\u043e\u043f\u0435\u0441-\u041a\u043e\u0431\u043e\u0441) - 1991, FLAC (tracks+.cue) lossless",
            "BBC Music Magazine December 2024 (vol.33 no.2): Szymanowski - Songs of the Fairy Tale Princess \u2022 Zemlinsky - Die Seejungfrau / Mermaid (BBC Symphony Orchestra, Sakari Oramo, BBC National Orchestra of Wales, Ryan Bancroft, Anu Komsi) - 2024, FLAC (image+.cue) lossless",
            "Szymanowski - Symphony No.3 'Song of the Night'; Symphony No.4 'Symphonie Concertante'; Concert Overture (Polish State Philharmonic Chorus & Orchestra <Katowice>, Karol Stryja) - 2019, FLAC (image+.cue) lossless",
            "\u0421\u0442\u0440\u0430\u0432\u0438\u043d\u0441\u043a\u0438\u0439 - \u0412\u0435\u0441\u043d\u0430 \u0441\u0432\u044f\u0449\u0435\u043d\u043d\u0430\u044f, \u0421\u0432\u0430\u0434\u0435\u0431\u043a\u0430 / Stravinsky - The Rite of Spring, Les Noces (Oakland Symphony Chorus, Magen Solomon, Redwood Symphony, Eric Kujawsky) - 1993, FLAC Gold CD (image+.cue) lossless",
            "Nielsen - Complete Symphonies, Aladdin Suite, Little Suite For Strings, Hymnis Amoris, Maskarade (Danish National Radio Choir, Danish National Symphony Orchestra, Ulf Schirmer; San Francisco Symphony Chorus, San Francisco Symphony, Herbert Blomstedt) - 2014, FLAC (tracks) lossless",
            "Magnard - Hymne A Venus, Hymne A La Justice, Chant Funebre, Ouverture Op. 10, Suite Dans Le Style Ancien (Orchestre Philharmonique Du Luxembourg, Mark Stringer) - 2002, FLAC (tracks) lossless",
            "\u0410\u043b\u0435\u043a\u0441\u0430\u043d\u0434\u0440 \u0413\u043b\u0430\u0437\u0443\u043d\u043e\u0432 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u044f \u21164 \u2022 \u0414\u043c\u0438\u0442\u0440\u0438\u0439 \u041a\u0430\u0431\u0430\u043b\u0435\u0432\u0441\u043a\u0438\u0439 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u044f \u21162 (\u0416\u0430\u043a \u0420\u0430\u0445\u043c\u0438\u043b\u043e\u0432\u0438\u0447) / Alexander Glazunov - Symphony No.4 \u2022 Dmitry Kabalevsky - Symphony No.2 (Orchestra dell'Accademia Nazionale di Santa Cecilia - Jacques Rachmilovich) - 2021, FLAC (tracks+.cue) lossless",
            "Holst - Planets (LSO, Ambrosian Singers, Andre Previn) - 2012, FLAC XRCD24 (image+.cue) lossless",
            "Mozart - Serenades and Divertimenti: KV 136, 137, 239 & 525 (Camerata Academica Salzburg, Sandor Vegh) - 1987, XRCD24 FLAC (image+.cue) lossless",
            "Kabel\u00e1\u010d / Kabelac - Mystery of Time; Hamlet Improvisation; Reflections; Metamorphoses II (Miroslav Sekera, Prague Radio Symphony Orchestra, Marko Ivanovi\u0107 / Ivanovic) - 2022, FLAC (image+.cue) lossless",
            "Vivarte. The First 10 Years: Agricola, Bach, Beethoven, Gabrieli, Handel, Haydn, Marenzio, Mozart, Onslow, Praetorius, Purcell, Schubert, Tallis, Vivaldi, Weber, Weiss, Werrecore (Niederaltaicher Scholaren, Ruhland; Huelgas Ensemble, Nevel, etc) - 1999, FLAC (image+.cue) lossless",
            "Anton Bruckner - Symphonie Nr. 6 / Symphony No. 6 (Berliner Philharmoniker - Riccardo Muti) / \u0410\u043d\u0442\u043e\u043d \u0411\u0440\u0443\u043a\u043d\u0435\u0440 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u044f \u2116 6 (\u0420\u0438\u043a\u0430\u0440\u0434\u043e \u041c\u0443\u0442\u0438) - 1988, FLAC (tracks+.cue) lossless",
            "Franck - Symphony in D minor; Redemption; Le Chasseur maudit (Frankfurt Radio Symphony, Alain Altinoglu) - 2022, FLAC (image+.cue) lossless",
            "Beethoven - Violin Concerto \u2022 Stravinsky / \u0421\u0442\u0440\u0430\u0432\u0438\u043d\u0441\u043a\u0438\u0439 - Symphony in 3 Movements \u2022 Ravel - Daphnis et Chloe Suite no.2 (Frank Peter Zimmermann; The New York Philharmonic, Alan Gilbert) - 2012, FLAC (image+.cue) lossless",
            "Vivaldi - Seine Beliebten Werke: Concerto per Archi e Cembalo; Concerti Grossi Nos. 8 & 10 op. 3; Sinfonia \u2022 Corelli - Sarabande, Giga, Badinerie (I Solisti di Zagreb) - 1989, FLAC (image+.cue) lossless",
            "Anton Bruckner - Symphonie Nr. 6 / Symphony No. 6 (Schleswig-Holstein Music Festival Orchestra - Christoph Eschenbach) / \u0410\u043d\u0442\u043e\u043d \u0411\u0440\u0443\u043a\u043d\u0435\u0440 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u044f \u2116 6 (\u041a\u0440\u0438\u0441\u0442\u043e\u0444 \u042d\u0448\u0435\u043d\u0431\u0430\u0445) - 1989, FLAC (tracks+.cue) lossless",
            "Mozart - Symphonies Nos. 35 'Haffner', 36 'Linz' & 40 (The Deutsche Kammerphilharmonie Bremen, Tarmo Peltokoski) - 2024, FLAC (image+.cue) lossless",
            "La Valse \u00b7 L'arlesienne - French Orchestral Favorites: Bizet, Chabrier, Debussy, Ibert, Ravel (Tokyo Metropolitan Symphony Orchestra, Jean Fournet) - 1987, FLAC (image+.cue) lossless",
            "Delius - Brigg Fair; La Calinda from Koanga; Intermezzo and Serenade from Hassan; A Song Before Sunrise; On Hearing the First Cuckoo in Spring; The Walk to the Paradise Garden; Irmelin prelude (The Royal Philharmonic Orchestra, Christopher Seaman) - 1993, FLAC (image+.cue) lossless",
            "Brahms - Hungarian Dances \u2022 Dvorak / Dvo\u0159\u00e1k - Slavonic Dances (Gewandhausorchester Leipzig, Kurt Masur) - 1990, FLAC (tracks+.cue) lossless",
            "Walton - The Quest, The Wise Virgins, Siesta (English Northern Philharmonia, David Lloyd-Jones) - 2002, FLAC (tracks) lossless",
            "Nielsen - Aladdin Suite, Pan And Syrinx, Saga Dream, Maskarade Overture, Helios Overture, Cupid and the Poet (South Jutland Symphony Orchestra, Niklas Willen) - 2005, FLAC (tracks) lossless",
            "Suk - Fairy Tale, Fantasy In G Minor, Fantastic Scherzo (Michael Ludwig, Buffalo Philharmonic Orchestra, JoAnn Falletta) - 2011, FLAC (tracks) lossless",
            "Brahms - Symphony No. 3, Haydn Variations (London Philharmonic Orchestra, Marin Alsop) - 2007, FLAC (tracks) lossless",
            "Carl Schuricht dirigiert Dresdner Philharmonie: Debussy - Prelude a l'Apres-midi d'un faune \u00b7 Mozart - Symphonies Nos. / Symphonien Nrn. 23 & 34 \u00b7 Brahms - Akademische Festouverture / Academic Festival Overture - 1995, FLAC (tracks+.cue) lossless",
            "Anton Bruckner - Symphonie Nr. 5 / Symphony No. 5 (Gewandhausorchester Leipzig - Franz Konwitschny) / \u0410\u043d\u0442\u043e\u043d \u0411\u0440\u0443\u043a\u043d\u0435\u0440 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u044f \u2116 5 (\u0424\u0440\u0430\u043d\u0446 \u041a\u043e\u043d\u0432\u0438\u0447\u043d\u044b\u0439) - 1993, FLAC (tracks+.cue) lossless",
            "BBC Music Magazine November 2024 (vol 33, no 1): Gustav Holst - The Hymn of Jesus \u2022 Claude Debussy - Pelleas et Melisande \u2022 Michael Tippett - Symphony no.4 (Andrew Davis, BBC Symphony Orchestra, BBC Symphony Chorus, BBC Philharmonic) - 2024, FLAC (image+.cue) lossless",
            "Anna Thorvaldsdottir - Archora / Aion (Iceland Symphony Orchestra, Eva Ollikainen) - 2023, FLAC (image+.cue) lossless",
            "Joe Hisaishi in Vienna - Symphony No.2; Viola Saga (Antoine Tamestit, Wiener Symphoniker, Joe Hisaishi) - 2024, FLAC (image+.cue) lossless",
            "Anton Bruckner - Symphonie Nr. 5 / Symphony No. 5 (Bruckner Orchester Linz - Martin Sieghart) / \u0410\u043d\u0442\u043e\u043d \u0411\u0440\u0443\u043a\u043d\u0435\u0440 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u044f \u2116 5 (\u041c\u0430\u0440\u0442\u0438\u043d \u0417\u0438\u0433\u0445\u0430\u0440\u0442) - 1996, FLAC (tracks+.cue) lossless",
            "Harty - Complete Orchestral Works (Heather Harper, Ralph Holmes, Malcolm Binns; Ulster Orchestra, Bryden Thomson) - 2004, FLAC (tracks) lossless",
            "Adams - City Noir; Fearful Symmetries; Lola Montez Does the Spider Dance (ORF Vienna Radio Symphony Orchestra, Marin Alsop) - 2024, FLAC (image+.cue) lossless",
            "\u0421\u0442\u0440\u0430\u0432\u0438\u043d\u0441\u043a\u0438\u0439 / Stravinsky - Symphony in Three Movements; Symphonies of Wind Instruments; Symphony in C (Orquesta Sinfonica de Galicia, Dima Slobodeniouk / \u0421\u043b\u043e\u0431\u043e\u0434\u0435\u043d\u044e\u043a) - 2024, FLAC (image+.cue) lossless",
            "Anton Bruckner - Symphonie Nr. 4 \u00bbRomantische\u00ab / Symphony No. 4 \"Romantic\" (Radio-Sinfonie-Orchester Berlin - Karl Richter) / \u0410\u043d\u0442\u043e\u043d \u0411\u0440\u0443\u043a\u043d\u0435\u0440 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u044f \u2116 4 \"\u0420\u043e\u043c\u0430\u043d\u0442\u0438\u0447\u0435\u0441\u043a\u0430\u044f\" (\u041a\u0430\u0440\u043b \u0420\u0438\u0445\u0442\u0435\u0440) - 2003, FLAC (tracks+.cue) lossless",
            "Kaiserwalzer: Johann Strauss Jr. - An der schonen, blauen Donau; G'schichten aus dem Wienerwald \u2022 Johann Strauss Sr. - Radetzky-Marsch (Radio-Symphonie-Orchester Berlin, Ferenc Fricsay) - 1989, FLAC (image+.cue) lossless",
            "George Philipp Telemann - Tafelmusik / Musique de Table (Musica Amphion: Wilbert Hazelzet, Kate Clark, Remy Baudet, Franc Polman, Sayuri Yamagata, Richte van der Meer, Jaap ter Linden, William Wroth, etc; Pieter-Jan Belder, Remy Baudet) [4 CDs] - 2006/2014, FLAC (image+.cue) lossless",
            "Dukas - The Sorcerer's Apprentice (Berliner Philharmoniker, James Levine) - 2009, FLAC (tracks) lossless",
            "Anton Bruckner - Symphonie Nr. 4 \u00bbRomantische\u00ab / Symphony No. 4 \"Romantic\" (Residentie Orkest - Hans Vonk) / \u0410\u043d\u0442\u043e\u043d \u0411\u0440\u0443\u043a\u043d\u0435\u0440 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u044f \u2116 4 \"\u0420\u043e\u043c\u0430\u043d\u0442\u0438\u0447\u0435\u0441\u043a\u0430\u044f\" (\u0425\u0430\u043d\u0441 \u0424\u043e\u043d\u043a) - 1985, FLAC (tracks+.cue) lossless",
            "Anton Bruckner - Symphonie Nr. 4 \u00bbRomantische\u00ab / Symphony No. 4 \"Romantic\" (BBC Scottish Symphony Orchestra - Ion Marin) / \u0410\u043d\u0442\u043e\u043d \u0411\u0440\u0443\u043a\u043d\u0435\u0440 - \u0421\u0438\u043c\u0444\u043e\u043d\u0438\u044f \u2116 4 \"\u0420\u043e\u043c\u0430\u043d\u0442\u0438\u0447\u0435\u0441\u043a\u0430\u044f\" (\u0418\u043e\u043d \u041c\u0430\u0440\u0438\u043d) - 2004, FLAC (tracks+.cue) lossless",
            "Franz Krommer - Symphonies Nos. 4, 5 & 7 (Orchestra della Svizzera italiana, Howard Griffiths) - 2017, FLAC (image+.cue) lossless"
        ]
        url_item = module.URLItem(
            url='https://rutracker.org',
            id='classical',
            # cleaner=lambda x: x,
            max_bodies_per_notif=3,
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
