'''Provides bindings to the tvdb api.'''

from pytvdbapi import api
from pytvdbapi.error import TVDBIndexError

from yajuu.config import config


class TheTvDbProvider:

    '''Helper class to get data from thetvdb api.'''

    def _get_result(self, query, select_result):
        # First, fetch the show itself

        not_found_exception = self.MediaNotFoundException(
            'Could not find the anime on thetvdb.'
        )

        database = api.TVDB(config['thetvdb']['api_key'])

        try:
            results = database.search(query, config['thetvdb']['language'])

            if len(results) == 0:
                raise not_found_exception
            elif len(results) == 1:
                show = results[0]
            else:
                identifier = select_result(list(
                    (x.id, x.SeriesName) for x in results
                ))

                # We'll use the last iteration show variable
                for show in results:
                    if show.id == identifier:
                        break

            # Fetch the metadata
            show.update()
        except TVDBIndexError:
            raise not_found_exception

        return show
