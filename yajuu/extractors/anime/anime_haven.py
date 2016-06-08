import re
import urllib.parse

import requests
from bs4 import BeautifulSoup
import cfscrape

from .anime_extractor import AnimeExtractor


class AnimeHavenExtractor(AnimeExtractor):
    def search(self):
        # Remove all the unnecessary signs
        response = requests.post(
            'http://animehaven.org/wp-admin/admin-ajax.php',
            data={
                'action': 'search_ajax',
                'keyword': self.media.metadata['name']
            }
        ).text.replace('\\n', '').replace('\\t', '').replace('\\', '')

        soup = BeautifulSoup(response, 'html.parser')

        results = []

        for result in soup.find_all('div', {'class': 'sa_post'}):
            title_block = result.find('h6')
            link = title_block.find('a')  # The first one is the good one
            title, href = link.get('title'), link.get('href')

            versions_soup = BeautifulSoup(
                requests.get(href).text, 'html.parser'
            )

            versions = list(
                ('Sub' if 'sub' in x.text.lower() else 'Dub', x.get('href'))
                for x in versions_soup.find_all('a', {'class': 'ah_button'})
            )

            for version, url in versions:
                results.append(('{} ({})'.format(title, version), url))

        return results

    def extract(self, season, result):
        page = 1
        pages = 1
        pages_url_base = None
        url = result[1]

        page_regex = re.compile(r'(http://.+/page/)([0-9]+)')
        episode_regex = re.compile(r'http://.+-episode-([0-9]+)')
        tiwi_kiwi_regex = re.compile(r'[0-9]+x([0-9]+), .+ [a-zA-Z]+')
        tiwi_kiwi_onclick_regex = re.compile(
            r"download_video\('(.+)','(.+)','(.+)'\)"
        )

        discovered_episodes = []

        while page <= pages:
            soup = BeautifulSoup(requests.get(url).text, 'html.parser')

            if page == 1:
                pagination_links = soup.find(
                    'nav', {'class': 'pagination'}
                ).find_all('a')

                page_regex_results = re.search(
                    page_regex, pagination_links[-1].get('href')
                )

                pages_url_base = page_regex_results.group(1)
                pages = int(page_regex_results.group(2))

            episodes = soup.find_all('article', {'class': 'post'})
            discovered_episodes += list(
                x.find('h2').find('a').get('href') for x in episodes
            )

            page += 1
            url = pages_url_base + str(page)

        sources = {}

        for link in discovered_episodes:
            episode_number_search = re.search(episode_regex, link)

            if not episode_number_search:
                continue

            episode_number = int(episode_number_search.group(1))
            print('[AnimeHaven] Processing episode {}'.format(episode_number))

            soup = BeautifulSoup(requests.get(link).text, 'html.parser')

            download_div = soup.find('div', {'class': 'download_feed_link'})

            if not download_div:
                continue

            download_links = list(
                (x.find('span'), x.get('href'))
                for x in download_div.find_all('a')
            )

            if episode_number not in sources:
                sources[episode_number] = []

            for quality_span, url in download_links:
                if quality_span is not None:
                    quality = int(
                        ''.join(x for x in quality_span.text if x.isdigit())
                    )

                    sources[episode_number].append((quality, url))
                elif (
                    quality_span is None and
                    urllib.parse.urlsplit(url).netloc == 'tiwi.kiwi'
                ):
                    s = requests.session()

                    tiwi_kiwi_soup = BeautifulSoup(
                        s.get(url).text, 'html.parser'
                    )

                    download_table = tiwi_kiwi_soup.find('table', {
                        'class': 'tbl1'
                    })

                    if not download_table:
                        continue

                    for tr in download_table.find_all('tr'):
                        if len(tr.find_all('a')) > 0:
                            quality_regex = re.search(
                                tiwi_kiwi_regex,
                                tr.find_all('td')[1].text
                            )

                            if not quality_regex:
                                continue

                            quality = int(quality_regex.group(1))

                            onclick_regex_result = re.search(
                                tiwi_kiwi_onclick_regex,
                                tr.find('a').get('onclick')
                            )

                            if not onclick_regex_result:
                                continue

                            code = onclick_regex_result.group(1)
                            mode = onclick_regex_result.group(2)
                            hash = onclick_regex_result.group(3)

                            url = (
                                'http://tiwi.kiwi/dl?op=download_orig&id={}&'
                                'mode={}&hash={}'.format(code, mode, hash)
                            )

                            retries = 10
                            retry = 0

                            while retry < retries:
                                download_soup = BeautifulSoup(
                                    s.get(url).text, 'html.parser'
                                )

                                span = download_soup.find('div', {
                                    'id': 'container'
                                }).find('span')

                                if not span:
                                    retry += 1
                                    print('-> retries={}/{}'.format(
                                        retry, retries
                                    ))
                                    continue

                                link = span.find('a').get('href')

                                sources[episode_number].append((quality, link))
                                break

        return sources
