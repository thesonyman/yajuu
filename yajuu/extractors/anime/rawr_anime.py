import concurrent.futures

import requests
from bs4 import BeautifulSoup

from yajuu.extractors.anime import AnimeExtractor
from yajuu.extractors import unshorten, SearchResult


class RawrAnimeExtractor(AnimeExtractor):

    def _get_url(self):
        return 'http://rawranime.tv'

    def search(self):
        html = requests.get('http://rawranime.tv/index.php', params={
            'ajax': 'anime',
            'do': 'search',
            's': self.media.metadata['name']
        }).text.replace('\\', '')

        soup = BeautifulSoup(html, 'html.parser')

        results = []

        for link in soup.find_all('a'):
            title = link.find('div', {'class': 'quicksearch-title'}).text
            id = link.get('href')  # With a leading slash

            results += [
                (title + ' (Sub)', ('Subbed', id)),
                (title + ' (Dub)', ('Dubbed', id))
            ]

        return SearchResult.from_tuples(self.media, results)

    def extract(self, season, result):
        version, id = result
        url = 'http://rawranime.tv' + id + '?apl=1'

        html = requests.get(url).json()['html']
        soup = BeautifulSoup(html, 'html.parser')

        episodes = []

        for episode in soup.find_all('div', {'class': 'ep '}):
            number_div = episode.find('div', {'class': 'ep-number'})
            episodes.append((version, id, number_div.text))

        self.logger.debug('Found {} episodes'.format(len(episodes)))

        sources = {}

        with concurrent.futures.ThreadPoolExecutor(16) as executor:
            list(executor.map(self.page_worker, episodes))

    def page_worker(self, data):
        version, id, number = data
        number = int(number)

        self.logger.debug('Processing episode {}'.format(number))

        id = id[7:]  # Remove '/anime'

        url = 'http://rawranime.tv/watch/{}/episode-{}'.format(id, number)
        soup = self._get(url)

        elements = soup.find_all(
            lambda x: x.name == 'div' and x.has_attr('data-src') and
            x.has_attr('data-quality')
        )

        for element in elements:
            if element.get('data-lang').lower() != version.lower():
                continue

            quality = int(''.join(
                x for x in element.get('data-quality') if x.isdigit()
            ))

            src = element.get('data-src')

            self.logger.debug('Unshortening {}, quality {}p'.format(
                src, quality
            ))

            self._add_sources(number, unshorten(src, quality=quality))

        self.logger.debug('Done processing episode {}'.format(number))
