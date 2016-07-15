import re
import json
import concurrent.futures

import js2py

from . import AnimeExtractor
from .. import unshorten


class MasteraniExtractor(AnimeExtractor):
    MIRRORS_REGEX = re.compile(r'var args = ({[.\s\S]+?)</script>')

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

        return results

    def extract(self, season, result):
        id, slug = result[1]

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

        # We extract the object hard-coded, and translate it to json.
        javascript = 'JSON.stringify({})'.format(
            self.MIRRORS_REGEX.search(self.session.get(url).text).group(1)
        )

        self.logger.debug(javascript)

        mirrors = json.loads(js2py.eval_js(javascript))['mirrors']

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
