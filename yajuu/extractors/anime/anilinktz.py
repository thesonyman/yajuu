import concurrent.futures
import urllib.parse
import re

from bs4 import BeautifulSoup

from yajuu.extractors.anime import AnimeExtractor
from yajuu.extractors import SearchResult, unshorten
from yajuu.media import Source


class AnilinktzExtractor(AnimeExtractor):

    def _get_url(self):
        return 'http://anilinkz.tv/'

    def search(self):
        # You actually really need to lower the query, else the search method
        # just returns an empty list every time.
        soup = self._get('http://anilinkz.tv/search', params={
            'q': self.media.metadata['name'].lower()
        })

        return SearchResult.from_links(
            self.media, soup.select('ul#seariessearchlist a[title]')
        )

    def extract(self, season, result):
        soup = self._get('http://anilinkz.tv' + result)
        episodes = [
            x.get('href') for x in soup.select('#serieslist span span a')
        ]

        with concurrent.futures.ThreadPoolExecutor(16) as executor:
            list(executor.map(self._episode_worker, episodes))

    def _episode_worker(self, url):
        episode_number = int(re.search(r'-episode-(\d{1,3})$', url).group(1))

        self.logger.info('Processing episode {}'.format(episode_number))

        url = 'http://anilinkz.tv' + url
        soup = self._get(url)
        self._parse_source(episode_number, url, soup)

        for link in soup.select('#sources a')[1:]:
            url = 'http://anilinkz.tv' + link.get('href')
            self._parse_source(episode_number, url, self._get(url))

        self.logger.info('Done processing episode {}'.format(episode_number))

    def _parse_source(self, identifier, url, soup):
        script = soup.find(
            'script', text=re.compile(r'^document.write\(unescape')
        )

        if script is None:
            self.logger.warning('Could not process {}'.format(url))
            return

        embed_js = urllib.parse.unquote(
            re.sub(r'([A-Z\~\!\@\#\$\*\{\}\[\]\-\+\.])', '', script.text)
        )

        iframe_src = BeautifulSoup(
            embed_js, 'html.parser'
        ).find('iframe').get('src')

        self._add_sources(identifier, unshorten(iframe_src))
