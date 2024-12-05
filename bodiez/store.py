from dataclasses import dataclass, field
from glob import glob
import json
import os
import time
from typing import List
from urllib.parse import quote
import uuid

from google.cloud import firestore


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

    def _get_filename(self):
        return f'{int(time.time() * 1000)}-{str(uuid.uuid4())[:8]}.json'

    def _get_url_dir(self, url):
        return os.path.join(self.base_dir, quote(url, safe=''))

    def _list_url_files(self, url):
        return sorted(glob(os.path.join(self._get_url_dir(url), '*.json')))

    def get(self, url):
        files = self._list_url_files(url)
        if not files:
            return Document(url=url)
        with open(files[-1], 'r', encoding='utf-8') as fd:
            return Document(**json.load(fd))

    def set(self, url, bodies):
        url_dir = self._get_url_dir(url)
        if not os.path.exists(url_dir):
            os.makedirs(url_dir)
        file = os.path.join(url_dir, self._get_filename())
        data = {
            'url': url,
            'bodies': bodies,
            'updated_ts': int(time.time()),
        }
        with open(file, 'w', encoding='utf-8') as fd:
            json.dump(data, fd, sort_keys=True, indent=4)
        for f in self._list_url_files(url):
            if f != file:
                os.remove(f)


def get_store(config):
    if os.path.exists(config.GOOGLE_CREDS):
        return Firestore(config)
    return SharedStore(config)
