from dataclasses import dataclass, field
import json
import logging
import re
import time
from urllib.parse import urlparse, unquote_plus

from svcutils.service import Notifier

from bodiez import NAME, logger
from bodiez.store import get_store
from bodiez.parsers.base import iterate_parsers


MAX_NOTIF_PER_URL = 4
MAX_NOTIF_BODY_SIZE = 500

logging.getLogger('selenium').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)


def get_url_netloc_token(url):
    parts = urlparse(url).netloc.split('.')
    out_parts = parts[1:] if parts[0] == 'www' else parts
    return '.'.join(out_parts[:-1])


def clean_body(body):
    res = re.sub(r'\(.*?\)', '', body).strip()
    res = re.sub(r'\[.*?\]', '', res).strip()
    res = re.sub(r'[\(][^\(]*$|[\[][^\[]*$', '', res).strip()
    return res or body


@dataclass
class URLItem:
    url: str
    id: str = None
    update_delta: int = 3600
    allow_no_results: bool = False
    params: dict = field(default_factory=dict)

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
        self.store = get_store(self.config)
        self.max_notif_per_url = (self.config.MAX_NOTIF_PER_URL
            or MAX_NOTIF_PER_URL)

    def _notify_new_bodies(self, url_item, bodies):
        notif_title = f'{NAME} {url_item.id}'
        rev_bodies = [clean_body(r) for r in reversed(bodies)]
        max_latest = self.max_notif_per_url - 1
        latest_bodies = rev_bodies[-max_latest:]
        older_bodies = rev_bodies[:-max_latest]
        if older_bodies:
            body = ', '.join(reversed(older_bodies))
            if len(body) > MAX_NOTIF_BODY_SIZE:
                body = f'{body[:MAX_NOTIF_BODY_SIZE]}...'
            Notifier().send(title=notif_title, body=f'{body}')
        for body in latest_bodies:
            Notifier().send(title=notif_title, body=body)

    def _iterate_parsers(self, url_item):
        for parser_cls in self.parsers:
            if parser_cls.can_parse(url_item):
                yield parser_cls(self.config)

    def _collect_bodies(self, url_item):
        start_ts = time.time()
        parsers = list(self._iterate_parsers(url_item))
        if not parsers:
            raise Exception('no available parser')
        res = []
        for parser in sorted(parsers, key=lambda x: x.id):
            bodies = [r for r in parser.parse(url_item) if r]
            if not bodies:
                logger.info(f'no result for {url_item.id} '
                    f'using parser {parser.id}')
                continue
            res.extend(bodies)
        logger.debug(f'parser {parser.id} collected bodies for '
            f'{url_item.id}:\n{json.dumps(bodies, indent=4)}')
        logger.info(f'collected {len(res)} bodies for {url_item.id} in '
            f'{time.time() - start_ts:.02f} seconds')
        return res

    def _process_url_item(self, url_item):
        start_ts = time.time()
        doc = self.store.get(url_item.url)
        if not (self.force or doc.updated_ts <
                time.time() - url_item.update_delta):
            logger.debug(f'skipped recently updated {url_item.id}')
            return
        bodies = self._collect_bodies(url_item)
        if not (bodies or url_item.allow_no_results):
            raise Exception('no result')
        new_bodies = [r for r in bodies if r not in doc.bodies]
        if new_bodies:
            logger.info(f'new bodies for {url_item.id}:\n'
                f'{json.dumps(new_bodies, indent=4)}')
            self._notify_new_bodies(url_item, new_bodies)
        bodies_history = [r for r in doc.bodies if r not in bodies]
        self.store.set(url_item.url, bodies + bodies_history[
            :max(self.config.MIN_BODIES_HISTORY, len(bodies))])
        logger.info(f'processed {url_item.id} in '
            f'{time.time() - start_ts:.02f} seconds')

    def run(self, url_id=None):
        start_ts = time.time()
        for item in self.config.URLS:
            url_item = URLItem(**item)
            if url_id and url_item.id != url_id:
                continue
            try:
                self._process_url_item(url_item)
            except Exception as exc:
                logger.exception(f'failed to process {url_item}')
                Notifier().send(title=f'{NAME} error',
                    body=f'{url_item.id}: {exc}')
        logger.info(f'processed in {time.time() - start_ts:.02f} seconds')


def collect(config, force=False, url_id=None):
    Collector(config, force=force).run(url_id)
