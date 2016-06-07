from .anime_extractor import AnimeExtractor

import requests
import urllib.parse


class HtvanimeExtractor(AnimeExtractor):
    def search(self):
        # Fetch all the pages
        page = 0
        pages_count = 1
        results = []

        while page < pages_count:
            response = requests.post(
                'https://sjzdlecc2z-dsn.algolia.net/1/indexes/Anime/query?x-'
                'algolia-agent=Algolia%20for%20vanilla%20JavaScript%203.14.6&x'
                '-algolia-application-id=SJZDLECC2Z&x-algolia-api-key='
                'caa4878bcf6f8aea380e73b5840ff22b',

                json={
                    'params': urllib.parse.urlencode({
                        'query': self.media.metadata['name'],
                        'hitsPerPage': 10,
                        'page': page
                    })
                }
            ).json()

            page += 1

            pages_count = int(response['nbPages'])

            for hit in response['hits']:
                results.append((hit['title'], hit['slug']))

        return results
