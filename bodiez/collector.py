from glob import glob
import hashlib
import json
import logging
import os
import re
import shutil
import time
from urllib.parse import urlparse, unquote_plus
from uuid import uuid4

from svcutils.service import Notifier
from webutils.browser import get_driver

from bodiez import NAME, logger
from bodiez.parsers.base import iterate_parsers


MAX_NOTIF_PER_URL = 4
MAX_NOTIF_BODY_SIZE = 500
STORAGE_RETENTION_DELTA = 7 * 24 * 3600

logging.getLogger('selenium').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)


def makedirs(x):
    if not os.path.exists(x):
        os.makedirs(x)


def get_file_mtime(x):
    return os.stat(x).st_mtime


def clean_title(title):
    res = re.sub(r'\(.*?\)', '', title).strip()
    res = re.sub(r'\[.*?\]', '', res).strip()
    res = re.sub(r'[\(][^\(]*$|[\[][^\[]*$', '', res).strip()
    return res or title


class TitleStorage:
    def __init__(self, base_path):
        self.base_path = os.path.realpath(base_path)

    def _get_dst_dirname(self, url):
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def _get_dst_path(self, url):
        return os.path.join(self.base_path, self._get_dst_dirname(url))

    def _generate_dst_filename(self):
        return f'{uuid4().hex}.json'

    def _iterate_file_and_titles(self, url):
        for file in glob(os.path.join(self._get_dst_path(url), '*.json')):
            try:
                with open(file, 'r', encoding='utf-8') as fd:
                    titles = json.load(fd)
            except Exception:
                logger.exception(f'failed to load file {file}')
                continue
            yield file, titles

    def _load_titles(self, url):
        res = {}
        for file, titles in self._iterate_file_and_titles(url):
            res.update(titles)
        return res

    def get_new_titles(self, url, titles):
        stored_titles = self._load_titles(url)
        return {k: v for k, v in titles.items() if k not in stored_titles}

    def save(self, url, all_titles, new_titles):
        all_title_keys = set(all_titles.keys())
        for file, titles in self._iterate_file_and_titles(url):
            if not set(titles.keys()) & all_title_keys:
                os.remove(file)
                logger.debug(f'removed old file {file}')

        dst_path = self._get_dst_path(url)
        makedirs(dst_path)
        file = os.path.join(dst_path, self._generate_dst_filename())
        with open(file, 'w', encoding='utf-8') as fd:
            json.dump(new_titles, fd, sort_keys=True, indent=4)

    def cleanup(self, all_urls):
        dirnames = {self._get_dst_dirname(r) for r in all_urls}
        min_ts = time.time() - STORAGE_RETENTION_DELTA
        for path in glob(os.path.join(self.base_path, '*')):
            if os.path.basename(path) in dirnames:
                continue
            mtimes = [get_file_mtime(r)
                for r in glob(os.path.join(path, '*'))]
            if not mtimes or max(mtimes) < min_ts:
                shutil.rmtree(path)
                logger.info(f'removed old storage path {path}')


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


class TitleCollector:
    def __init__(self, config, headless=True):
        self.config = config
        self.driver = get_driver(
            browser_id=self.config.BROWSER_ID,
            headless=headless,
            page_load_strategy='eager',
        )
        self.parsers = list(iterate_parsers())
        self.title_storage = TitleStorage(self.config.STORAGE_PATH)

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
                yield parser_cls(self.driver)

    def _collect_titles(self, url_item):
        parsers = list(self._iterate_parsers(url_item))
        if not parsers:
            raise Exception('no available parser')
        res = {}
        now = time.time()
        for parser in sorted(parsers, key=lambda x: x.id):
            titles = [r for r in parser.parse(url_item.url) if r]
            logger.debug(f'{parser.id} results ({url_item.url}):\n'
                f'{json.dumps(titles, indent=4)}')
            if not titles:
                logger.error(f'no result from {url_item.url}')
                Notifier().send(title=f'{NAME} error',
                    body=f'no result from {parser.id}')
                continue
            res.update({r: now - i for i, r in enumerate(titles)})
        return res

    def _process_url_item(self, url_item):
        titles = self._collect_titles(url_item)
        if not titles:
            raise Exception('no result')
        logger.info(f'parsed {len(titles)} titles from {url_item.url}')
        new_titles = self.title_storage.get_new_titles(url_item.url, titles)
        if new_titles:
            self._notify_new_titles(url_item, new_titles)
            self.title_storage.save(url_item.url, titles, new_titles)

    def run(self):
        start_ts = time.time()
        urls = set()
        try:
            for url in self.config.URLS:
                url_item = URLItem(url)
                urls.add(url_item.url)
                try:
                    self._process_url_item(url_item)
                except Exception as exc:
                    logger.exception(f'failed to process {url_item}')
                    Notifier().send(title=f'{NAME} error',
                        body=f'failed to process {url_item.id}: {exc}')
        finally:
            self.driver.quit()
        self.title_storage.cleanup(urls)
        logger.info(f'processed in {time.time() - start_ts:.02f} seconds')


def collect(config, headless=True):
    TitleCollector(config, headless=headless).run()
