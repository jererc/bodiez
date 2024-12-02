from dataclasses import dataclass
import json
import logging
import re
import time
from urllib.parse import urlparse, unquote_plus

from svcutils.service import Notifier

from bodiez import NAME, logger
from bodiez.firestore import FireStore
from bodiez.parsers.base import iterate_parsers


MAX_NOTIF_PER_URL = 4
MAX_NOTIF_BODY_SIZE = 500

logging.getLogger('selenium').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)


def get_url_netloc_token(url):
    parts = urlparse(url).netloc.split('.')
    out_parts = parts[1:] if parts[0] == 'www' else parts
    return '.'.join(out_parts[:-1])


def clean_title(title):
    res = re.sub(r'\(.*?\)', '', title).strip()
    res = re.sub(r'\[.*?\]', '', res).strip()
    res = re.sub(r'[\(][^\(]*$|[\[][^\[]*$', '', res).strip()
    return res or title


@dataclass
class URLItem:
    url: str
    id: str = None
    update_delta: int = 3600
    allow_no_results: bool = False

    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()

    def _generate_id(self):
        parsed = urlparse(unquote_plus(self.url))
        words = re.findall(r'\b\w+\b', f'{parsed.path} {parsed.query}')
        return '-'.join([get_url_netloc_token(self.url)]
            + [r for r in words if len(r) > 1])


class Collector:
    def __init__(self, config, force=False):
        self.config = config
        self.force = force
        self.parsers = list(iterate_parsers())
        self.store = FireStore(self.config)
        self.max_notif_per_url = (self.config.MAX_NOTIF_PER_URL
            or MAX_NOTIF_PER_URL)

    def _notify_new_titles(self, url_item, titles):
        notif_title = f'{NAME} {url_item.id}'
        rev_titles = [clean_title(r) for r in reversed(titles)]
        max_latest = self.max_notif_per_url - 1
        latest_titles = rev_titles[-max_latest:]
        older_titles = rev_titles[:-max_latest]
        if older_titles:
            body = ', '.join(reversed(older_titles))
            if len(body) > MAX_NOTIF_BODY_SIZE:
                body = f'{body[:MAX_NOTIF_BODY_SIZE]}...'
            Notifier().send(title=notif_title, body=f'{body}')
        for title in latest_titles:
            Notifier().send(title=notif_title, body=title)

    def _iterate_parsers(self, url_item):
        for parser_cls in self.parsers:
            if parser_cls.can_parse_url(url_item.url):
                yield parser_cls(self.config)

    def _collect_titles(self, url_item):
        start_ts = time.time()
        parsers = list(self._iterate_parsers(url_item))
        if not parsers:
            raise Exception('no available parser')
        res = []
        for parser in sorted(parsers, key=lambda x: x.id):
            titles = [r for r in parser.parse(url_item) if r]
            if not titles:
                logger.info(f'no result for {url_item} '
                    f'using parser {parser.id}')
                continue
            res.extend(titles)
        logger.info(f'collected {len(res)} titles for {url_item} in '
            f'{time.time() - start_ts:.02f} seconds')
        return res

    def _process_url_item(self, url_item):
        start_ts = time.time()
        doc = self.store.get(url_item.url)
        if not (self.force or doc.updated_ts <
                time.time() - url_item.update_delta):
            logger.debug(f'skipped recently updated {url_item}')
            return
        titles = self._collect_titles(url_item)
        if not (titles or url_item.allow_no_results):
            raise Exception('no result')
        new_titles = [r for r in titles if r not in doc.titles]
        if new_titles:
            logger.info(f'new titles for {url_item}:\n'
                f'{json.dumps(new_titles, indent=4)}')
            self._notify_new_titles(url_item, new_titles)
        titles_history = [r for r in doc.titles if r not in titles]
        self.store.set(url_item.url, titles + titles_history[
            :max(self.config.MIN_TITLES_HISTORY, len(titles))])
        logger.info(f'processed {url_item} in '
            f'{time.time() - start_ts:.02f} seconds')

    def run(self):
        start_ts = time.time()
        for item in self.config.URLS:
            url_item = URLItem(**item)
            try:
                self._process_url_item(url_item)
            except Exception as exc:
                logger.exception(f'failed to process {url_item}')
                Notifier().send(title=f'{NAME} error',
                    body=f'{url_item.id}: {exc}')
        logger.info(f'processed in {time.time() - start_ts:.02f} seconds')


def collect(config, force=False):
    Collector(config, force=force).run()
