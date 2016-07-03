from pytvdbapi import api
from pytvdbapi.error import TVDBIndexError

from yajuu.config import config


class TheTvDbMedia:
    '''Helper class to get data from thetvdb api.'''

    def __eq__(self, other):
        return (
            isinstante(other, self.__class__) and
            self.metadata['id'] == other.metadata['id']
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def _get_result(self, query, select_result):
        # First, fetch the show itself

        not_found_exception = self.MediaNotFoundException(
            'Could not find the anime on thetvdb.'
        )

        db = api.TVDB(config['thetvdb']['api_key'])

        try:
            results = db.search(query, config['thetvdb']['language'])

            if len(results) == 0:
                raise not_found_exception
            elif len(results) == 1:
                show = results[0]
            else:
                show = select_result(query, results)

            # Fetch the metadata
            show.update()
        except TVDBIndexError:
            raise not_found_exception

        return show
