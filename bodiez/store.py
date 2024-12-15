from dataclasses import asdict, dataclass, field
from glob import glob
import hashlib
import json
import os
from pprint import pformat
import socket
import time
from typing import List

from bodiez import logger


HOSTNAME = socket.gethostname()


@dataclass
class Document:
    url: str
    titles: List[str] = field(default_factory=list)
    updated_ts: int = 0
    ref: str = None


class CloudSyncStore:
    def __init__(self, config):
        self.config = config
        self.base_dir = self.config.STORE_DIR
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def _get_doc_id(self, url):
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def _list_files(self, url):
        return sorted(glob(os.path.join(self.base_dir,
            f'{self._get_doc_id(url)}-*.json')))

    def _get_file(self, url):
        return os.path.join(self.base_dir, f'{self._get_doc_id(url)}-'
            f'{int(time.time() * 1000)}-{HOSTNAME}.json')

    def get(self, url):
        try:
            file = self._list_files(url)[-1]
        except IndexError:
            return Document(url=url)
        with open(file, 'r', encoding='utf-8') as fd:
            doc = Document(**json.load(fd))
        if doc.url != url:   # MEGA sync bug
            logger.error(f'mismatching doc for {url} ({file}):\n'
                f'{pformat(asdict(doc), width=160)}')
            raise Exception(f'mismatching doc for {url}')
        return doc

    def set(self, url, titles):
        old_files = self._list_files(url)[:-1]
        file = self._get_file(url)
        data = {
            'url': url,
            'titles': titles,
            'updated_ts': int(time.time()),
            'ref': file,
        }
        with open(file, 'w', encoding='utf-8') as fd:
            json.dump(data, fd, sort_keys=True, indent=4)
        for f in old_files:
            os.remove(f)
