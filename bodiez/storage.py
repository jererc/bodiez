from dataclasses import dataclass, asdict
from glob import glob
import hashlib
import json
import os
import shutil
import time
from uuid import uuid4

from bodiez import logger


RETENTION_DELTA = 7 * 24 * 3600


def get_file_mtime(x):
    return os.stat(x).st_mtime


@dataclass
class URLTitle:
    url: str
    title: str
    ts: int

    def to_dict(self):
        return asdict(self)


class SharedLocalStore:
    def __init__(self, config):
        self.config = config
        self.base_path = os.path.realpath(self.config.STORAGE_PATH)

    def _get_dst_dirname(self, url):
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def _get_dst_path(self, url):
        return os.path.join(self.base_path, self._get_dst_dirname(url))

    def _generate_dst_filename(self):
        return f'{uuid4().hex}.json'

    def _iterate_file_and_url_titles(self, url):
        for file in glob(os.path.join(self._get_dst_path(url), '*.json')):
            try:
                with open(file, 'r', encoding='utf-8') as fd:
                    data = json.load(fd)
                url_titles = [URLTitle(**r) for r in data]
            except Exception:
                logger.exception(f'failed to load file {file}')
                continue
            yield file, url_titles

    def _load_url_titles(self, url):
        url_titles = []
        for file, file_url_titles in self._iterate_file_and_url_titles(url):
            url_titles.extend(file_url_titles)
        return url_titles

    def get_new_titles(self, url, url_titles):
        titles = {r.title for r in self._load_url_titles(url)}
        return [r for r in url_titles if r.title not in titles]

    def _purge_other_url_titles(self, url, url_titles):
        if not url_titles:
            return
        titles = {r.title for r in url_titles}
        cutoff_ts = time.time() - RETENTION_DELTA

        def must_be_removed(url_titles):
            for ut in url_titles:
                if ut.ts > cutoff_ts or ut.title in titles:
                    return False
            return True

        for file, file_url_titles in self._iterate_file_and_url_titles(url):
            if must_be_removed(file_url_titles):
                os.remove(file)

    def save(self, url, new_url_titles, url_titles):
        dst_path = self._get_dst_path(url)
        if not os.path.exists(dst_path):
            os.makedirs(dst_path)
        file = os.path.join(dst_path, self._generate_dst_filename())
        data = [r.to_dict() for r in new_url_titles]
        with open(file, 'w', encoding='utf-8') as fd:
            json.dump(data, fd, sort_keys=True, indent=4)
        self._purge_other_url_titles(url, url_titles)

    def cleanup(self, urls):
        dirnames = {self._get_dst_dirname(r) for r in urls}
        cutoff_ts = time.time() - RETENTION_DELTA
        for path in glob(os.path.join(self.base_path, '*')):
            if os.path.basename(path) in dirnames:
                continue
            mtimes = [get_file_mtime(r)
                for r in glob(os.path.join(path, '*'))]
            if not mtimes or max(mtimes) < cutoff_ts:
                shutil.rmtree(path)
                logger.info(f'removed old storage path {path}')
