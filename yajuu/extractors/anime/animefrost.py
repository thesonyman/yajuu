import concurrent.futures
import re

from yajuu.extractors.anime.anime_extractor import AnimeExtractor
from yajuu.extractors.search_result import SearchResult
from yajuu.unshorteners import unshorten
from yajuu.media.sources.source import Source


class AnimeFrostExtractor(AnimeExtractor):

    def _get_url(self):
        return 'http://beta.animefrost.tv/'

    def search(self):
        soup = self._get('http://beta.animefrost.tv', params={
            's': self.media.metadata['name']
        })

        return SearchResult.from_links(self.media, soup.select('.wrap a'))

    def extract(self, season, result):
        soup = self._get(result)
        episodes = [x.get('href') for x in soup.select('.episodes a')]

        with concurrent.futures.ThreadPoolExecutor(16) as executor:
            list(executor.map(self._episode_worker, episodes))

    def _episode_worker(self, url):
        episode_number = int(re.search(
            r'/s/\d+/episode/(\d{1,3})', url
        ).group(1))

        self.logger.info('Processing episode {}'.format(episode_number))

        soup = self._get(url)
        src = soup.find('iframe', {'id': 'ep-video'}).get('src')

        self._add_sources(episode_number, unshorten(src))
        self.logger.info('Done processing episode {}'.format(episode_number))
