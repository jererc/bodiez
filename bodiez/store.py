from dataclasses import asdict, dataclass, field
from glob import glob
import hashlib
import json
import os
from pprint import pformat
import socket
import time
from typing import List
from urllib.parse import urlparse

from bodiez import logger


HOSTNAME = socket.gethostname()


class State:
    def __init__(self, base_dir, url):
        self.file = os.path.join(base_dir, f'{urlparse(url).netloc}.json')
        os.makedirs(base_dir, exist_ok=True)

    def load(self):
        try:
            with open(self.file, 'r', encoding='utf-8') as fd:
                return json.load(fd)
        except FileNotFoundError:
            return None

    def save(self, state):
        with open(self.file, 'w', encoding='utf-8') as fd:
            fd.write(json.dumps(state))


@dataclass
class Document:
    url: str
    keys: List[str] = field(default_factory=list)
    updated_ts: int = 0
    ref: str = None


class CloudSyncStore:
    def __init__(self, config):
        self.config = config
        self.base_dir = self.config.STORE_DIR
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_doc_id(self, url):
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def _load_doc(self, file):
        with open(file, 'r', encoding='utf-8') as fd:
            return Document(**json.load(fd))

    def get(self, url):
        files = glob(os.path.join(self.base_dir,
            f'{self._get_doc_id(url)}-*.json'))
        if not files:
            return Document(url=url)
        doc = sorted([self._load_doc(r) for r in files],
            key=lambda x: x.updated_ts)[-1]
        if doc.url != url:
            logger.error(f'mismatching doc for {url}:\n'
                f'{pformat(asdict(doc), width=160)}')
            raise Exception(f'mismatching doc for {url}')
        return doc

    def set(self, url, keys):
        file = os.path.join(self.base_dir,
            f'{self._get_doc_id(url)}-{HOSTNAME}.json')
        data = {
            'url': url,
            'keys': keys,
            'updated_ts': time.time(),
            'ref': file,
        }
        with open(file, 'w', encoding='utf-8') as fd:
            json.dump(data, fd, sort_keys=True, indent=4)
