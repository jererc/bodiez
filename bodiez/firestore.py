import os
import time

from google.cloud import firestore

from bodiez import WORK_PATH, logger
from bodiez.storage import RETENTION_DELTA


DEFAULT_GOOGLE_CREDS = os.path.join(WORK_PATH, 'google.json')


def generate_batches(items, batch_size):
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


class FireStore:
    collection_name = 'bodiez'

    def __init__(self, config):
        self.config = config
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = (
            self.config.GOOGLE_CREDS or DEFAULT_GOOGLE_CREDS)
        self.db = firestore.Client()

    def _iterate_url_docs(self, url):
        query = (self.db.collection(self.collection_name)
            .where('url', '==', url)
        )
        for doc in query.stream():
            yield doc

    def _delete_docs(self, docs):
        for docs_batch in generate_batches(docs, batch_size=500):
            batch = self.db.batch()
            for doc in docs_batch:
                batch.delete(doc.reference)
            batch.commit()

    def get_new_titles(self, url, url_titles):
        titles = {r.to_dict()['title'] for r in self._iterate_url_docs(url)}
        return [r for r in url_titles if r.title not in titles]

    def _purge_other_docs(self, url, url_titles):
        if not url_titles:
            return

        titles = {r.title for r in url_titles}
        cutoff_ts = time.time() - RETENTION_DELTA

        def must_be_deleted(x):
            return x['title'] not in titles and x['ts'] < cutoff_ts

        docs = [r for r in self._iterate_url_docs(url)
            if must_be_deleted(r.to_dict())]
        self._delete_docs(docs)

    def save(self, url, new_url_titles, url_titles):
        if new_url_titles:
            to_upsert = [r.to_dict() for r in new_url_titles]
            batch = self.db.batch()
            for data in to_upsert:
                doc = self.db.collection(self.collection_name).document()
                batch.set(doc, data)
            batch.commit()
        self._purge_other_docs(url, url_titles)

    def cleanup(self, urls):
        cutoff_ts = time.time() - RETENTION_DELTA

        def must_be_deleted(x):
            return x['url'] not in urls and x['ts'] < cutoff_ts

        docs = [r for r in self.db.collection(self.collection_name).stream()
            if must_be_deleted(r.to_dict())]
        self._delete_docs(docs)
