from dataclasses import dataclass, field
from glob import glob
import hashlib
import json
import os
import time
from typing import List
from urllib.parse import quote
import uuid

from google.cloud import firestore

from bodiez import logger


@dataclass
class Document:
    url: str
    bodies: List[str] = field(default_factory=list)
    updated_ts: int = 0


class Firestore:
    def __init__(self, config):
        self.config = config
        self.db = firestore.Client.from_service_account_json(
            self.config.GOOGLE_CREDS)
        self.col = self.db.collection(self.config.FIRESTORE_COLLECTION)

    def _get_doc_id(self, url):
        return quote(url, safe='')

    def get(self, url):
        doc = self.col.document(self._get_doc_id(url)).get()
        return Document(**doc.to_dict()) if doc.exists else Document(url=url)

    def set(self, url, bodies):
        self.col.document(self._get_doc_id(url)).set({
            'url': url,
            'bodies': bodies,
            'updated_ts': int(time.time()),
        })


class SharedStore:
    def __init__(self, config):
        self.config = config
        self.base_dir = self.config.SHARED_STORE_DIR
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def _get_doc_id(self, url):
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def _list_files(self, url):
        return sorted(glob(os.path.join(self.base_dir,
            f'{self._get_doc_id(url)}-*.json')))

    def _get_file_ts(self, file):
        try:
            return int(os.path.basename(file).split('-')[1]) / 1000
        except Exception:
            logger.exception(f'failed to get ts from {file}')
            return 0

    def _get_file(self, url):
        return os.path.join(self.base_dir, f'{self._get_doc_id(url)}-'
            f'{int(time.time() * 1000)}-{str(uuid.uuid4())[:8]}.json')

    def get(self, url):
        files = self._list_files(url)
        if not files:
            return Document(url=url)
        with open(files[-1], 'r', encoding='utf-8') as fd:
            return Document(**json.load(fd))

    def set(self, url, bodies):
        file = self._get_file(url)
        data = {
            'url': url,
            'bodies': bodies,
            'updated_ts': int(time.time()),
        }
        with open(file, 'w', encoding='utf-8') as fd:
            json.dump(data, fd, sort_keys=True, indent=4)
        for sf in self._list_files(url):
            if sf != file and self._get_file_ts(sf) < time.time() - 60:
                os.remove(sf)


def get_store(config):
    if os.path.exists(config.GOOGLE_CREDS):
        logger.debug('using google firestore')
        return Firestore(config)
    logger.debug(f'using shared store {config.SHARED_STORE_DIR}')
    return SharedStore(config)
