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


def clean_title(title):
    res = re.sub(r'\([^)]*\)', '', title)
    res = re.sub(r'\[[^]]*\]', '', res)
    res = re.sub(r'\([^(]*$|\[[^[]*$', '', res)
    res = re.sub(r'\s{2,}', ' ', res)
    return res.strip()


def to_float(x):
    return float(f'{x:.02f}')


def to_json(x):
    return json.dumps(x, sort_keys=True, indent=4)


@dataclass
class Query:
    url: str
    id: str = None
    active: bool = True
    update_delta: int = 3600
    headless_timeout: int = 10
    headful_timeout: int = 60
    allow_no_results: bool = False
    block_external: bool = False
    block_images: bool = True
    xpath: str = None
    child_xpaths: List[str] = field(default_factory=list)
    group_attrs: List[str] = field(default_factory=list)
    rel_xpath: str = None
    link_xpath: str = '.'
    pages: int = 1
    text_delimiter: str = ', '
    max_notif: int = 3
    title_processor: any = clean_title

    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()
        if not self.title_processor:
            self.title_processor = lambda x: x

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

    def _notify_new_bodies(self, query, bodies):
        more_count = len(bodies[query.max_notif:])
        for i, body in enumerate(reversed(bodies[:query.max_notif])):
            body_str = query.title_processor(body.title) or body.title
            if i == 0 and more_count:
                body_str += f' (+{more_count} more)'
            Notifier().send(title=query.id, body=body_str,
                app_name=NAME, on_click=body.url)

    def _iterate_parsers(self, query):
        for parser_cls in self.parsers:
            parser = parser_cls(self.config, query)
            if parser.can_parse():
                yield parser

    def _collect_bodies(self, query):
        parsers = list(self._iterate_parsers(query))
        if not parsers:
            raise Exception('no available parser')
        res = []
        for parser in sorted(parsers, key=lambda x: x.id):
            bodies = [r for r in parser.parse() if r]
            logger.debug(f'collected {len(bodies)} bodies for {query.id}:\n'
                f'{to_json([asdict(r) for r in bodies])}')
            if not bodies:
                logger.info(f'no results for {query.id} '
                    f'with parser {parser.id}')
                continue
            res.extend(bodies)
        return res

    def _process_query(self, query):
        start_ts = time.time()
        doc = self.store.get(query.url)
        if not (self.force or self.test or doc.updated_ts <
                time.time() - query.update_delta):
            logger.debug(f'skipped recently updated {query.id}')
            return
        bodies = self._collect_bodies(query)
        if not (bodies or query.allow_no_results):
            raise Exception('no results')
        if self.test:
            self._notify_new_bodies(query, bodies)
            return
        new_bodies = [r for r in bodies if r.title not in doc.titles]
        if new_bodies:
            self._notify_new_bodies(query, new_bodies)
        titles = [r.title for r in bodies]
        history = [r for r in doc.titles if r not in titles]
        self.store.set(query.url, titles + history[
            :max(self.config.MIN_BODIES_HISTORY, len(titles))])
        self.report.append({
            'id': query.id,
            'collected': len(bodies),
            'new_bodies': [asdict(r) for r in new_bodies],
            'duration': to_float(time.time() - start_ts),
        })

    def run(self, url_id=None):
        start_ts = time.time()
        for query_args in self.config.QUERIES:
            query = Query(**query_args)
            if not (query.active or self.test):
                continue
            if url_id and query.id != url_id:
                continue
            logger.debug(f'processing {query.id}:\n'
                f'{pformat(asdict(query), width=160)}')
            try:
                self._process_query(query)
            except Exception as exc:
                logger.exception(f'failed to process {query.id}: {exc}')
                Notifier().send(title=query.id,
                    body=f'error: {exc}', app_name=NAME)
        if self.report:
            logger.info(f'report:\n{to_json(self.report)}')
        logger.info(f'processed in {time.time() - start_ts:.02f} seconds')


def collect(config, force=False):
    Collector(config, force=force).run()


def test(config, url_id=None):
    Collector(config, test=test).run(url_id)
