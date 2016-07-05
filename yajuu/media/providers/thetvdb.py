from pytvdbapi import api
from pytvdbapi.error import TVDBIndexError

from yajuu.config import config


class TheTvDbProvider:
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
                id = select_result(query, list(
                    (x.id, x.SeriesName) for x in results
                ))

                # We'll use the last iteration show variable
                for show in results:
                    if show.id == id:
                        break

            # Fetch the metadata
            show.update()
        except TVDBIndexError:
            raise not_found_exception

        return show
