import re
import concurrent.futures
import itertools

from . import AnimeExtractor
from .. import unshorten


class GogoAnimeIoExtractor(AnimeExtractor):
    def _get_url(self):
        return 'http://gogoanime.io'

    def search(self):
        self._disable_cloudflare()

        soup = self._post('http://gogoanime.io/site/loadSearch', data={
            'data': self.media.metadata['name'],
            'id': '-1'
        })

        results = []

        for item in soup.select('#header_search_autocomplete_body > div'):
            link = item.find('a')
            results.append((link.text.strip(), link.get('href')))

        return results

    def extract(self, season, result):
        soup = self._get(result[1])

        movie_id = soup.select('#movie_id')[0].get('value')
        default_ep = soup.select('#default_ep')[0].get('value')

        with concurrent.futures.ThreadPoolExecutor(16) as executor:
            links_by_block = executor.map(self._block_worker, (
                (movie_id, default_ep, x) for x in
                soup.select('#episode_page > li > a')
            ))

            # We need to flatten the array
            links = itertools.chain.from_iterable(links_by_block)

            sources = {}

            for source in executor.map(self._episode_worker, links):
                if source:
                    sources[source[0]] = source[1]

        return sources

    def _block_worker(self, data):
        movie_id, default_ep, link = data

        ep_start, ep_end = link.get('ep_start'), link.get('ep_end')

        block_url = (
            'http://gogoanime.io/site/loadEpisode?ep_start={}&ep_end='
            '{}&id={}&default_ep={}'
        ).format(ep_start, ep_end, movie_id, default_ep)

        block_soup = self._get(block_url)

        urls = []

        for link in block_soup.select('li > a'):
            urls.append(link.get('href').strip())

        return urls

    def _episode_worker(self, url):
        soup = self._get(url)
        episode_number = int(soup.select('#default_ep')[0].get('value'))

        print('[GogoAnimeIo] Processing episode', episode_number)

        sources = unshorten(
            soup.select('div.download-anime > a')[0].get('href')
        )

        print('[GogoAnimeIo] Done processing episode', episode_number)

        return (episode_number, sources)
