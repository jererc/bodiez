import time
from urllib.parse import quote

from google.cloud import firestore

from bodiez import logger


class FireStore:
    def __init__(self, config):
        self.config = config
        self.db = firestore.Client.from_service_account_json(
            self.config.GOOGLE_CREDS)
        self.col = self.db.collection(self.config.FIRESTORE_COLLECTION)

    def _get_doc_id(self, url):
        return quote(url, safe='')

    def _get_or_set(self, url):
        doc_id = self._get_doc_id(url)
        doc_ref = self.col.document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            logger.debug(f'loaded stored doc {doc_ref.id}')
            return {'ref': doc_ref, 'data': doc.to_dict()}
        data = {'url': url, 'titles': []}
        doc_ref.set(data)
        return {'ref': doc_ref, 'data': data}

    def get(self, url):
        return self._get_or_set(url)

    def update(self, doc_ref, titles=None):
        data = {'updated_ts': int(time.time())}
        if titles is not None:
            data['titles'] = titles
        doc_ref.update(data)
        return doc_ref
