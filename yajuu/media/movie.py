'''Provides the implementation of the movie class.'''

from yajuu.media.media import Media
from yajuu.media.providers.imdb import ImdbProvider
from yajuu.config import config


class Movie(ImdbProvider, Media):

    """Media class the defines an anime.

    Currently fetches data using the imdb provider.
    
    """

    def get_path_config(self):
        return config['path']['medias']['movie']

    def _update_metadata(self):
        item = self._get_result(self.query, self._select_result)

        self.metadata['id'] = item['imdb_id']
        self.metadata['name'] = item['title']
        self.metadata['year'] = item['year']
