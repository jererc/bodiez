import os
from urllib.parse import quote

from google.cloud import firestore

from bodiez import NAME, WORK_PATH, logger


DEFAULT_GOOGLE_CREDS = os.path.join(WORK_PATH, 'gcs.json')
DEFAULT_FIRESTORE_COLLECTION = NAME


class FireStore:
    def __init__(self, config):
        self.config = config
        self.collection_name = (self.config.FIRESTORE_COLLECTION
            or DEFAULT_FIRESTORE_COLLECTION)
        self.creds = self.config.GOOGLE_CREDS or DEFAULT_GOOGLE_CREDS
        self.db = firestore.Client.from_service_account_json(self.creds)
        self.col = self.db.collection(self.collection_name)

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

    def update_ref(self, doc_ref, titles):
        doc_ref.update({'titles': titles})
        logger.debug(f'updated doc {doc_ref.id} with {len(titles)}')
        return doc_ref
