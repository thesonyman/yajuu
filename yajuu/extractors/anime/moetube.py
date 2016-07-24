import re
import concurrent.futures

from yajuu.extractors.anime.anime_extractor import AnimeExtractor
from yajuu.extractors.search_result import SearchResult
from yajuu.extractors.unshorteners.utils import get_quality
from yajuu.media.sources.source import Source


class MoeTubeExtractor(AnimeExtractor):

    def _get_url(self):
        return 'http://moetube.net/'

    def search(self):
        soup = self._get('http://moetube.net/searchapi.php', params={
            'page': 1,
            'keyword': self.media.metadata['name']
        })

        results = []

        for link in soup.select('.series a'):
            title = link.find('div', {'id': 'stitle'}).text
            results.append((title, link.get('href')))

        return SearchResult.from_tuples(self.media, results)

    def extract(self, season, result):
        soup = self._get('http://moetube.net' + result)

        episodes_chunks = soup.select('#navmain a')
        episodes_chunks = episodes_chunks[1:]  # Remove the summary page
        episodes_chunks = [x.get('href') for x in episodes_chunks]
        self.logger.debug(episodes_chunks)

        # The links to the episodes
        episodes = []

        for link in episodes_chunks:
            soup = self._get('http://moetube.net' + link)
            episodes += [x.get('href') for x in soup.select('.episode > a')]

        self._episode_worker(episodes[0])

        # with concurrent.futures.ThreadPoolExecutor(16) as executor:
        #     list(executor.map(self._episode_worker, episodes))

    def _episode_worker(self, link):
        # First extract the anime and episodes ids
        results = re.search(r'/watch/([0-9]+)/.+?/([0-9]+)', link)
        id = results.group(1)
        episode_number = int(results.group(2))

        self.logger.info('Processing episode {}'.format(episode_number))

        # Then get the downlaod link
        src = self.session.post('http://moetube.net/rui.php', data={
            'id': id,
            'ep': episode_number,
            'chk': 1
        }).text

        try:
            quality = get_quality(src)
        except:
            return

        self._add_source(episode_number, Source(src, quality))
        self.logger.info('Done processing episode {}'.format(episode_number))
