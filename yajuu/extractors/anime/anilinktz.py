import concurrent.futures
import urllib.parse
import re

from bs4 import BeautifulSoup

from yajuu.extractors.anime.anime_extractor import AnimeExtractor
from yajuu.extractors.search_result import SearchResult
from yajuu.unshorteners import unshorten
from yajuu.media.sources.source import Source


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
        url = 'http://anilinkz.tv' + result
        response, soup = self._get(url, return_response=True)

        page_count = int(re.search(
            r"\$\('#pagenavi'\).pagination\({\s+pages:\s(\d+),", response.text
        ).group(1))
        pages = [url + '?page={}'.format(x) for x in range(2, page_count)]

        episodes = self._list_episodes(soup)

        for page in pages:
            soup = self._get(page)
            episodes += self._list_episodes(soup)

        with concurrent.futures.ThreadPoolExecutor(16) as executor:
            list(executor.map(self._episode_worker, episodes))

    def _list_episodes(self, soup):
        return [
            x.get('href') for x in soup.select('#serieslist span span a')
        ]

    def _episode_worker(self, url):
        try:
            results = re.search(r'-episode-(\d{1,3})$', url)
            episode_number = int(results.group(1))
        except AttributeError:
            return

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
