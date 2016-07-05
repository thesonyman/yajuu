from imdbpie import Imdb

from yajuu.config import config


class ImdbProvider:
    '''Helper class to get data from thetvdb api.'''

    def __eq__(self, other):
        return (
            isinstante(other, self.__class__) and
            self.metadata['id'] == other.metadata['id']
        )

    def __ne__(self, other):
        return not self.__eq__(other)

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

            id = select_result(query, formatted_results)

            for item in results:
                if item['imdb_id'] == id:
                    break

        return item
