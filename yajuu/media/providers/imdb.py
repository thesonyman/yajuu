'''Provides bindings to the imdb api.'''

from imdbpie import Imdb


class ImdbProvider:

    '''Helper class to get data from thetvdb api.'''

    def _get_result(self, query, select_result):
        not_found_exception = self.MediaNotFoundException(
            'Could not find the anime on thetvdb.'
        )

        imdb = Imdb(cache=True)
        results = imdb.search_for_title(query)

        if len(results) == 0:
            raise not_found_exception
        elif len(results) == 1:
            item = results[0]
        else:
            formatted_results = list([
                (x['imdb_id'], '{} ({})'.format(x['title'], x['year']))
                for x in results
            ])

            identifier = select_result(query, formatted_results)

            for item in results:
                if item['imdb_id'] == identifier:
                    break

        return item
