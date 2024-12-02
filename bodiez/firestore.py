from dataclasses import dataclass, field
from typing import List
import time
from urllib.parse import quote

from google.cloud import firestore


@dataclass
class Document:
    url: str
    titles: List[str] = field(default_factory=list)
    updated_ts: int = 0


class FireStore:
    def __init__(self, config):
        self.config = config
        self.db = firestore.Client.from_service_account_json(
            self.config.GOOGLE_CREDS)
        self.col = self.db.collection(self.config.FIRESTORE_COLLECTION)

    def _get_doc_id(self, url):
        return quote(url, safe='')

    def get(self, url):
        doc_ref = self.col.document(self._get_doc_id(url))
        doc = doc_ref.get()
        return Document(**doc.to_dict()) if doc.exists else Document(url=url)

    def set(self, url, titles=None):
        data = {
            'url': url,
            'updated_ts': int(time.time()),
        }
        if titles is not None:
            data['titles'] = titles
        self.col.document(self._get_doc_id(url)).set(data)
