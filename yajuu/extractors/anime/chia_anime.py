import re
import concurrent.futures

import requests

from yajuu.extractors.anime.anime_extractor import AnimeExtractor
from yajuu.extractors.search_result import SearchResult


class ChiaAnimeExtractor(AnimeExtractor):

    def _get_url(self):
        return 'http://m.chia-anime.tv'

    def search(self):
        soup = self._get('http://m.chia-anime.tv/catlist.php', data={
            'tags': self.media.metadata['name']
        })

        results = []

        for link in soup.select('div.title > a'):
            results.append((
                link.text,
                ('http://m.chia-anime.tv' + link.get('href'))
            ))

        return SearchResult.from_tuples(self.media, results)

    def extract(self, season, result):
        soup = self._get(result)
        episodes_select = soup.find('select', {'id': 'id'})

        base_url = 'http://m.chia-anime.tv/mw.php?id={}&submit=Watch'

        episodes = []
        number_regex = re.compile(r'^Select .+? Episode (\d+)$')

        for option in episodes_select.find_all('option'):
            url = base_url.format(option.get('value'))

            number_regex_result = number_regex.search(option.text.strip())

            if not number_regex_result:
                self.logger.warning('Episode at url {} is invalid'.format(
                    url
                ))

                continue

            episodes.append((
                int(number_regex_result.group(1)),
                url
            ))

            self.logger.debug(base_url.format(option.get('value')))

        with concurrent.futures.ThreadPoolExecutor(16) as executor:
            list(executor.map(self._page_worker, episodes))

    def _page_worker(self, data):
        episode_number, url = data

        self.logger.info('Processing episode {}'.format(episode_number))

        soup = self._get(url)

        self.logger.info('Done processing episode {}'.format(episode_number))
