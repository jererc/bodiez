from dataclasses import dataclass, field
import time
from typing import List
from urllib.parse import quote

from google.cloud import firestore


@dataclass
class Document:
    url: str
    bodies: List[str] = field(default_factory=list)
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
        doc = self.col.document(self._get_doc_id(url)).get()
        return Document(**doc.to_dict()) if doc.exists else Document(url=url)

    def set(self, url, bodies):
        self.col.document(self._get_doc_id(url)).set({
            'url': url,
            'bodies': bodies or [],
            'updated_ts': int(time.time()),
        })
