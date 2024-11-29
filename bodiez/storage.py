from glob import glob
import hashlib
import json
import os
import shutil
import time
from uuid import uuid4

from bodiez import logger


STORAGE_RETENTION_DELTA = 7 * 24 * 3600


def get_file_mtime(x):
    return os.stat(x).st_mtime


class SharedLocalStorage:
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
        if not os.path.exists(dst_path):
            os.makedirs(dst_path)
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
