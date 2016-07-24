import re
import json
import concurrent.futures
import threading
import json

from yajuu.extractors.anime.anime_extractor import AnimeExtractor
from yajuu.extractors.search_result import SearchResult
from yajuu.unshorteners import unshorten


class MasteraniExtractor(AnimeExtractor):
    def _get_url(self):
        return 'http://www.masterani.me'

    def search(self):
        data = self.session.get(
            'http://www.masterani.me/api/anime-search', params={
                'keyword': self.media.metadata['name']
            }
        ).json()

        results = []

        for item in data:
            results.append((item['title'], (item['id'], item['slug'])))

        return SearchResult.from_tuples(self.media, results)

    def extract(self, season, result):
        id, slug = result

        episodes = self.session.get(
            'http://www.masterani.me/api/anime/{}/detailed'.format(id)
        ).json()[0]['episodes']

        sources = {}

        with concurrent.futures.ThreadPoolExecutor(16) as executor:
            list(executor.map(self.episode_worker, [
                (slug, episode) for episode in episodes
            ]))

    def episode_worker(self, data):
        slug, episode_details = data

        number = int(episode_details['episode'])

        self.logger.info('Processing episode {}'.format(number))

        url = 'http://www.masterani.me/anime/watch/{}/{}'.format(slug, number)

        mirrors = json.loads(re.search(
            r'var args = {[\s\S\n]+mirrors:[\s\S\n]+(\[.+?\]),[\s\S\n]+episode'
            r':',
            self.session.get(url).text
        ).group(1).strip().replace('\n', ''))

        for mirror in mirrors:
            prefix = mirror['host']['embed_prefix']
            suffix = mirror['host']['embed_suffix']

            if not prefix:
                prefix = ''

            if not suffix:
                suffix = ''

            url = prefix + mirror['embed_id'] + suffix

            self.logger.debug('Found mirror source: {}'.format(url))

            sources = unshorten(url, quality=mirror['quality'])
            self._add_sources(number, sources)

        self.logger.info('Done processing episode {}'.format(number))
