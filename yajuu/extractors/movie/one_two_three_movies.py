import re

import requests
from bs4 import BeautifulSoup

from yajuu.extractors.movie.movie_extractor import MovieExtractor
from yajuu.extractors.search_result import SearchResult
from yajuu.media.sources.source import Source
from yajuu.unshorteners import unshorten


class OneTwoThreeMoviesExtactor(MovieExtractor):

    def _get_url(self):
        return 'http://123movies.to/'

    def search(self):
        html = requests.post(
            self._get_url() + 'ajax/suggest_search', data={
                'keyword': self.media.metadata['name']
            }
        ).json()['content']

        soup = BeautifulSoup(html, 'html.parser')
        return SearchResult.from_links(self.media, soup.find_all(
            'a', {'class': 'ss-title'}
        ))

    def extract(self, result):
        id = re.search(r'/.+?-(\d+)/$', result).group(1)
        soup = self._get('http://123movies.to/ajax/v2_get_episodes/{}'.format(
            id
        ))

        urls = [(
            x.get('episode-id'),
            requests.get(
                'http://123movies.to/ajax/load_embed/' + x.get('episode-id')
            ).json()['embed_url']
        ) for x in soup.find_all('a', {'class': 'btn-eps'})]

        data = []

        for episode_id, url in urls:
            if url != '':
                try:
                    self._add_sources(unshorten(url))
                except:
                    pass
