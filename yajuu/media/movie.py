import datetime

from . import Media, ImdbProvider


class Movie(ImdbProvider, Media):
    def get_name(self):
        return 'Movie'

    def _update_metadata(self, query):
        item = self._get_result(query, self._select_result)

        self.metadata['id'] = item['imdb_id']
        self.metadata['name'] = item['title']
        self.metadata['year'] = item['year']

    def list_files(self):
        return []

    def download(self):
        pass
