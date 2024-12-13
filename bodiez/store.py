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
    titles: List[str] = field(default_factory=list)
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

    def set(self, url, titles):
        self.col.document(self._get_doc_id(url)).set({
            'url': url,
            'titles': titles,
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

    def _get_file(self, url):
        return os.path.join(self.base_dir, f'{self._get_doc_id(url)}-'
            f'{int(time.time() * 1000)}-{str(uuid.uuid4())[:8]}.json')

    def get(self, url):
        files = self._list_files(url)
        if not files:
            logger.debug(f'no stored document for {url}')
            return Document(url=url)
        file = files[-1]
        with open(file, 'r', encoding='utf-8') as fd:
            data = json.load(fd)
        if not data.get('titles'):
            logger.warning(f'loaded file without titles {file}')
        return Document(**data)

    def set(self, url, titles):
        old_files = self._list_files(url)[:-1]
        file = self._get_file(url)
        data = {
            'url': url,
            'titles': titles,
            'updated_ts': int(time.time()),
        }
        with open(file, 'w', encoding='utf-8') as fd:
            json.dump(data, fd, sort_keys=True, indent=4)
        for f in old_files:
            os.remove(f)


def get_store(config):
    if os.path.exists(config.GOOGLE_CREDS):
        logger.debug('using google firestore')
        return Firestore(config)
    logger.debug(f'using shared store {config.SHARED_STORE_DIR}')
    return SharedStore(config)
