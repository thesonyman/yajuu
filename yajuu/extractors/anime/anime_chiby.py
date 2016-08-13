import re
import copy
import time
import json
import concurrent.futures

import requests

from yajuu.extractors.anime.anime_extractor import AnimeExtractor
from yajuu.extractors.search_result import SearchResult
from yajuu.unshorteners import unshorten

HTTP_HEADER = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like '
        'Gecko) Chrome/47.0.2526.111 Safari/537.36'
    ),
    'Accept': (
        'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    ),
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Connection': 'keep-alive',
    'Accept-Language': 'nl-NL,nl;q=0.8,en-US;q=0.6,en;q=0.4',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
}


class AnimeChibyExtractor(AnimeExtractor):

    def _get_url(self):
        return 'http://www.animechiby.com'

    def search(self):
        soup = self._get('http://www.animechiby.com', params={
            's': self.media.metadata['name']
        })

        # Those are only 'top-level' links. The site organize contents in such
        # a way that the users can post an item, and in this item, multiple
        # medias can be found. We wanna fetch all those links.
        links = soup.select('.post h2 > a')

        # Well, the website uses window.open instead of href, for no apparent
        # reason.
        onclick_regex = r'window\.open\([\'|\'](.+)[\'|\']\);return false;'

        results = []

        for link in links:
            link_soup = self._get(link.get('href'))

            # We get all the available sub-links for each link
            for section in link_soup.select('.su-spoiler'):
                # The section title
                sub_title = section.select('.su-spoiler-title')[0].text

                # We get all the sources.
                available_sources = list((
                    x.get('value'),
                    re.search(onclick_regex, x.get('onclick')).group(1)
                ) for x in section.find_all('input'))

                self.logger.debug('Section {} has {} sources'.format(
                    sub_title, len(available_sources)
                ))

                # We determine the section title, that is the top-level title
                # concatenated with the section title.
                block_title = '-> {} ({})'.format(link.text, sub_title)

                results.append((block_title, available_sources))

        return SearchResult.from_tuples(self.media, results)

    def _unshorten(self, link):
        self.logger.debug('Unshortening {}'.format(link))

        request = requests.get(link, headers=HTTP_HEADER)

        session_id = re.findall(r'sessionId\:(.*?)\"\,', request.text)

        if len(session_id) <= 0:
            return

        session_id = re.sub(r'\s\"', '', session_id[0])

        http_header = copy.copy(HTTP_HEADER)
        http_header['Content-Type'] = 'application/x-www-form-urlencoded'
        http_header['Host'] = 'sh.st'
        http_header['Referer'] = link
        http_header['Origin'] = 'http://sh.st'
        http_header['X-Requested-With'] = 'XMLHttpRequest'

        time.sleep(5)

        payload = {'adSessionId': session_id, 'callback': 'c'}

        request = requests.get(
            'http://sh.st/shortest-url/end-adsession',
            params=payload, headers=http_header
        )

        response = request.content[6:-2].decode('utf-8')

        if request.status_code != 200:
            return

        resp_uri = json.loads(response)['destinationUrl']

        if resp_uri is None:
            return

        return resp_uri

    def extract(self, season, result):
        with concurrent.futures.ThreadPoolExecutor(16) as executor:
            # The website offer two kinds of links. The first one offer
            # directly the episodes as the links. The second redirects to a
            # page which list the links.

            # There should not be mixed cases, but we never now. We will
            # process each case every time.
            first_case_links = []
            second_case_links = []

            for input_title, link in result:
                # If we are in the first case
                if len(link.split('=')) == 2:
                    # The url is separated from the url using an equal symbol,
                    # so there is no need to try and crack the service itself.
                    first_case_links.append((
                        input_title, link.split('=')[1]
                    ))
                else:
                    # In the second case, we don't need to input title. However
                    # we need to get real links.
                    link = self._unshorten(link)

                    if not link:
                        continue

                    soup = self._get(link)
                    second_case_links += soup.select('td a[target="_BLANK"]')

            first_case_sources = list(executor.map(
                self.map_first_case, first_case_links
            ))

            self.logger.debug('Found first cases: {}'.format(first_case_links))

            second_case_sources = list(executor.map(
                self.map_second_case, second_case_links
            ))

            self.logger.debug('Found second cases: {}'.format(
                second_case_links
            ))

    def map_first_case(self, data):
        '''For the first case, get the real link and extract the episode
        number.'''

        input_title, link = data

        try:
            episode_number = int(''.join(
                c for c in input_title if c.isdigit()
            ))
        except ValueError:
            return

        if not self._should_process(episode_number):
            return

        self.logger.info('Processing episode {}'.format(
            episode_number
        ))

        self._add_sources(episode_number, unshorten(link))

        self.logger.info('Done Processing episode {}'.format(
            episode_number
        ))

    def map_second_case(self, episode_link):
        '''For the second, get the page (below this method) and then extract
        the links from that page.'''

        # The string is formatted as '\s+Episode (\d+)\s+'
        episode_identifier = ''.join(
            x for x in (episode_link.previous_sibling.strip())
            if x.isdigit()
        )

        try:
            episode_number = int(episode_identifier)
        except:
            return None

        if not self._should_process(episode_number):
            return

        self.logger.info('Processing episode {}'.format(
            episode_number
        ))

        # The links are shortened there too..
        episode_link = self._unshorten(
            episode_link.get('href')
        )

        self._add_sources(episode_number, unshorten(episode_link))

        self.logger.info('[AnimeChiby] Finished processing episode {}'.format(
            episode_number
        ))
