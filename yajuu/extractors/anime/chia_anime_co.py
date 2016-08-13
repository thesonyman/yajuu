import concurrent.futures
import re

from yajuu.extractors.anime.anime_extractor import AnimeExtractor
from yajuu.extractors.search_result import SearchResult
from yajuu.unshorteners import unshorten
from yajuu.media.sources.source import Source


class ChiaAnimeCoExtractor(AnimeExtractor):

    def _get_url(self):
        return 'http://chiaanime.co/'

    def search(self):
        # The manual encoding is intentionnal: the server does not handle
        # encoded requests.
        soup = self._post(
            'http://chiaanime.co/SearchSuggest/index.php',
            params='type=Anime&keyword={}'.format(self.media.metadata['name']),
        )

        return SearchResult.from_links(self.media, soup.find_all('a'))

    def extract(self, season, result):
        soup = self._get(result)
        episodes = [x.get('href') for x in soup.select('#episode_related a')]

        with concurrent.futures.ThreadPoolExecutor(16) as executor:
            list(executor.map(self._episode_worker, episodes))

    def _episode_worker(self, url):
        results = re.search(r'/Watch/(\d+)/(.+)/episode-(\d{1,3})/', url)
        episode_number = int(results.group(3))

        if not self._should_process(episode_number):
            return

        self.logger.info('Processing episode {}'.format(episode_number))

        soup = self._post('http://chiaanime.co/lib/picasa.php', data={
            'id': results.group(1),
            'anime': results.group(2),
            'episode': episode_number,
            'player': 'html5'
        })

        for link in soup.select('#divDownload a'):
            quality = int(re.search(r'(\d+)p', link.text).group(1))
            self._add_source(episode_number, Source(link.get('href'), quality))

        self.logger.info('Done processing episode {}'.format(episode_number))
