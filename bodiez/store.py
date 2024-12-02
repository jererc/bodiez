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
        self.base_path = self.config.SHARED_STORE_PATH

    def _get_dirname(self, url):
        return quote(url, safe='')

    def _get_filename(self):
        return f'{int(time.time() * 1000)}-{str(uuid.uuid4())[:8]}.json'

    def _load_file(self, file):
        with open(file, 'r', encoding='utf-8') as fd:
            return json.load(fd)

    def _list_url_files(self, url):
        url_path = os.path.join(self.base_path, self._get_dirname(url))
        return sorted(glob(os.path.join(url_path, '*.json')))

    def get(self, url):
        files = self._list_url_files(url)
        if files:
            return Document(**self._load_file(files[-1]))
        return Document(url=url)

    def set(self, url, bodies):
        path = os.path.join(self.base_path, self._get_dirname(url))
        if not os.path.exists(path):
            os.makedirs(path)
        file = os.path.join(path, self._get_filename())
        data = {
            'url': url,
            'bodies': bodies,
            'updated_ts': int(time.time()),
        }
        with open(file, 'w', encoding='utf-8') as fd:
            json.dump(data, fd, sort_keys=True, indent=4)
        for file in self._list_url_files(url)[:-1]:
            os.remove(file)


def get_store(config):
    if os.path.exists(config.GOOGLE_CREDS):
        return Firestore(config)
    return SharedStore(config)
