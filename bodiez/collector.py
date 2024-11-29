import json
import logging
import re
import time
from urllib.parse import urlparse, unquote_plus

from svcutils.service import Notifier

from bodiez import NAME, logger
from bodiez.parsers.base import iterate_parsers
from bodiez.storage import SharedLocalStorage


MAX_NOTIF_PER_URL = 4
MAX_NOTIF_BODY_SIZE = 500

logging.getLogger('selenium').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)


def clean_title(title):
    res = re.sub(r'\(.*?\)', '', title).strip()
    res = re.sub(r'\[.*?\]', '', res).strip()
    res = re.sub(r'[\(][^\(]*$|[\[][^\[]*$', '', res).strip()
    return res or title


class URLItem:
    def __init__(self, url_item):
        if not isinstance(url_item, (list, tuple)):
            url_item = [url_item]
        self.url = url_item[0]
        try:
            self.id = url_item[1]
        except IndexError:
            self.id = self._get_default_id()

    def __repr__(self):
        return f'id: {self.id}, url: {self.url}'

    def _get_default_id(self):
        parsed = urlparse(unquote_plus(self.url))
        words = re.findall(r'\b\w+\b', f'{parsed.path} {parsed.query}')
        tokens = [urlparse(self.url).netloc] + [r for r in words if len(r) > 1]
        return '-'.join(tokens)


class Collector:
    def __init__(self, config, headless=True):
        self.config = config
        self.parsers = list(iterate_parsers())
        self.storage = SharedLocalStorage(self.config.STORAGE_PATH)

    def _notify_new_titles(self, url_item, titles):
        notif_title = f'{NAME} {url_item.id}'
        asc_titles = [clean_title(n) for n, _ in sorted(titles.items(),
            key=lambda x: x[1])]
        max_latest = MAX_NOTIF_PER_URL - 1
        latest_titles = asc_titles[-max_latest:]
        older_titles = asc_titles[:-max_latest]
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
        parsers = list(self._iterate_parsers(url_item))
        if not parsers:
            raise Exception('no available parser')
        res = {}
        now = time.time()
        for parser in sorted(parsers, key=lambda x: x.id):
            titles = [r for r in parser.parse(url_item.url) if r]
            logger.debug(f'{parser.id} results for {url_item}:\n'
                f'{json.dumps(titles, indent=4)}')
            if not titles:
                logger.error(f'no result for {url_item}')
                continue
            res.update({r: now - i for i, r in enumerate(titles)})
        return res

    def _process_url_item(self, url_item):
        titles = self._collect_titles(url_item)
        if not titles:
            raise Exception('no result')
        logger.info(f'parsed {len(titles)} titles from {url_item.url}')
        new_titles = self.storage.get_new_titles(url_item.url, titles)
        if new_titles:
            self._notify_new_titles(url_item, new_titles)
            self.storage.save(url_item.url, titles, new_titles)

    def run(self):
        start_ts = time.time()
        urls = set()
        for url in self.config.URLS:
            url_item = URLItem(url)
            urls.add(url_item.url)
            try:
                self._process_url_item(url_item)
            except Exception as exc:
                logger.exception(f'failed to process {url_item}')
                Notifier().send(title=f'{NAME} error',
                    body=f'failed to process {url_item.id}: {exc}')
        self.storage.cleanup(urls)
        logger.info(f'processed in {time.time() - start_ts:.02f} seconds')


def collect(config):
    Collector(config).run()
