import concurrent.futures
import base64
import re

from yajuu.extractors.anime.anime_extractor import AnimeExtractor
from yajuu.extractors.search_result import SearchResult
from yajuu.extractors.unshorten import unshorten
from yajuu.media.sources.source import Source


class KissAnimeExtractor(AnimeExtractor):

    def _get_url(self):
        return 'http://kissanime.to'

    def search(self):
        self._disable_cloudflare()

        soup = self._post('http://kissanime.to/Search/SearchSuggest', data={
            'type': 'Anime',
            'keyword': self.media.metadata['name']
        })

        return SearchResult.from_links(self.media, soup.find_all('a'))

    def extract(self, season, result):
        soup = self._get(result)
        links = [x.get('href') for x in soup.select('td a')]

        with concurrent.futures.ThreadPoolExecutor(4) as executor:
            list(executor.map(self._episode_worker, links))

    def _episode_worker(self, link):
        episode_number = int(re.search(
            r'/Anime/.+?/Episode-(\d{3,})\?id=\d+$', link
        ).group(1))

        self.logger.info('Processing episode {}'.format(episode_number))

        response, soup = self._get(
            self._get_url() + link, return_response=True
        )

        quality_select = soup.find('select', {'id': 'selectQuality'})

        if quality_select is None:
            self.logger.warning('Could not extract sources, captcha required')
            return

        for option in quality_select:
            quality = int(''.join([x for x in option.text if x.isdigit()]))
            src = base64.b64decode(option.get('value')).decode('utf-8')
            self._add_source(episode_number, Source(src, quality))

        self.logger.info('Done processing episode {}'.format(episode_number))
