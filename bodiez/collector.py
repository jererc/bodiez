from dataclasses import asdict, dataclass, field
from pprint import pformat
import json
import re
import time
from typing import List
from urllib.parse import urlparse, unquote_plus

from svcutils.service import Notifier

from bodiez import NAME, logger
from bodiez.parsers.base import get_url_domain_name, iterate_parsers
from bodiez.store import get_store


def generate_batches(data, batch_size):
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]


def clean_body(body):
    res = re.sub(r'\([^)]*\)', '', body)
    res = re.sub(r'\[[^]]*\]', '', res)
    res = re.sub(r'\([^(]*$|\[[^[]*$', '', res)
    res = re.sub(r'\s{2,}', ' ', res)
    return res.strip() or body


def to_float(x):
    return float(f'{x:.02f}')


@dataclass
class URLItem:
    url: str
    id: str = None
    active: bool = True
    update_delta: int = 3600
    allow_no_results: bool = False
    block_external: bool = False
    block_images: bool = True
    xpath: str = None
    parent_xpath: str = None
    child_xpaths: List[str] = field(default_factory=list)
    multi_element_delimiter: str = ', '
    max_notif: int = 3
    max_bodies_per_notif: int = 1
    cleaner: any = clean_body

    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()
        if not self.cleaner:
            self.cleaner = lambda x: x

    def _generate_id(self):
        parsed = urlparse(unquote_plus(self.url))
        words = re.findall(r'\b\w+\b', f'{parsed.path} {parsed.query}')
        tokens = [get_url_domain_name(self.url)] + words
        return '-'.join([r for r in tokens if len(r) > 1])


class Collector:
    def __init__(self, config, force=False, test=False):
        self.config = config
        self.force = force
        self.test = test
        self.parsers = list(iterate_parsers())
        self.store = get_store(self.config)
        self.report = []

    def _notify_new_bodies(self, url_item, bodies):
        notif_title = f'{NAME} {url_item.id}'
        batches = list(generate_batches([url_item.cleaner(r) for r in bodies],
            batch_size=url_item.max_bodies_per_notif))
        for i, batch in enumerate(reversed(batches[:url_item.max_notif])):
            if i == 0 and len(batches) > url_item.max_notif:
                more = sum(len(r) for r in batches[url_item.max_notif:])
                batch[-1] += f' (+{more} more)'
            Notifier().send(title=notif_title, body='\r'.join(batch))

    def _iterate_parsers(self, url_item):
        for parser_cls in self.parsers:
            parser = parser_cls(self.config, url_item)
            if parser.can_parse():
                yield parser

    def _collect_bodies(self, url_item):
        parsers = list(self._iterate_parsers(url_item))
        if not parsers:
            raise Exception('no available parser')
        res = []
        for parser in sorted(parsers, key=lambda x: x.id):
            bodies = [r for r in parser.parse() if r]
            logger.debug(f'collected bodies for {url_item.id} '
                f'with parser {parser.id}:\n{pformat(bodies, width=160)}')
            if not bodies:
                logger.info(f'no results for {url_item.id} '
                    f'with parser {parser.id}')
                continue
            res.extend(bodies)
        return res

    def _process_url_item(self, url_item):
        start_ts = time.time()
        doc = self.store.get(url_item.url)
        if not (self.force or self.test or doc.updated_ts <
                time.time() - url_item.update_delta):
            logger.debug(f'skipped recently updated {url_item.id}')
            return
        parse_start_ts = time.time()
        bodies = self._collect_bodies(url_item)
        parsing_duration = time.time() - parse_start_ts
        if not (bodies or url_item.allow_no_results):
            raise Exception('no results')
        if self.test:
            self._notify_new_bodies(url_item, bodies)
            return
        new_bodies = [r for r in bodies if r not in doc.bodies]
        if new_bodies:
            self._notify_new_bodies(url_item, new_bodies)
        bodies_history = [r for r in doc.bodies if r not in bodies]
        self.store.set(url_item.url, bodies + bodies_history[
            :max(self.config.MIN_BODIES_HISTORY, len(bodies))])
        self.report.append({
            'id': url_item.id,
            'collected': len(bodies),
            'new_bodies': new_bodies,
            'parsing_duration': to_float(parsing_duration),
            'duration': to_float(time.time() - start_ts),
        })

    def run(self, url_id=None):
        start_ts = time.time()
        for item in self.config.URLS:
            url_item = URLItem(**item)
            if not (url_item.active or self.test):
                continue
            if url_id and url_item.id != url_id:
                continue
            logger.debug(f'processing {url_item.id}:\n'
                f'{pformat(asdict(url_item), width=160)}')
            try:
                self._process_url_item(url_item)
            except Exception as exc:
                logger.exception(f'failed to process {url_item.id}')
                Notifier().send(title=f'{NAME} {url_item.id}',
                    body=f'error: {exc}')
        if self.report:
            logger.info('report:\n'
                f'{json.dumps(self.report, sort_keys=True, indent=4)}')
        logger.info(f'processed in {time.time() - start_ts:.02f} seconds')


def collect(config, force=False):
    Collector(config, force=force).run()


def test(config, url_id=None):
    Collector(config, test=test).run(url_id)
