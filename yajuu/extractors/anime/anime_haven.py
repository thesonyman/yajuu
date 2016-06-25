import re
import concurrent.futures

from . import AnimeExtractor
from .. import unshorten


class AnimeHavenExtractor(AnimeExtractor):
    PAGE_REGEX = re.compile(r'(http://.+/page/)([0-9]+)')
    EPISODE_REGEX = re.compile(r'http://.+-episode-([0-9]+)')

    def search(self):
        soup = self._as_soup(
            'http://animehaven.org/wp-admin/admin-ajax.php',
            data={
                'action': 'search_ajax',
                'keyword': self.media.metadata['name']
            },
            strip=True
        )

        results = []

        for result in soup.find_all('div', {'class': 'sa_post'}):
            title_block = result.find('h6')
            link = title_block.find('a')  # The first one is the good one
            title, href = link.get('title'), link.get('href')

            versions_soup = self._as_soup(href)

            versions = list(
                ('Sub' if 'sub' in x.text.lower() else 'Dub', x.get('href'))
                for x in versions_soup.find_all('a', {'class': 'ah_button'})
            )

            for version, url in versions:
                results.append(('{} ({})'.format(title, version), url))

        return results

    def extract(self, season, result):
        self.default_url = result[1]

        with concurrent.futures.ThreadPoolExecutor(16) as executor:
            # First step, we extract links to all the episodes
            episodes, base_url, pages = self.page_worker(
                self.default_url
            )

            futures = []

            for page in pages:
                futures.append(executor.submit(
                    self.page_worker, base_url + str(page)
                ))

            results = concurrent.futures.wait(futures)

            for completed in results.done:
                episodes += completed.result()

            # Second step, we get all the available sources.
            sources = {}

            for source in executor.map(self.episode_worker, episodes):
                if source:
                    sources[source[0]] = source[1]

        return sources

    def page_worker(self, url):
        '''Extract the links to all the anime from the current page.'''

        soup = self._as_soup(url)

        # The episodes are listed on each page as posts.
        episodes = soup.find_all('article', {'class': 'post'})

        discovered_episodes = list(
            x.find('h2').find('a').get('href') for x in episodes
        )

        # For the first page, we use this method to determine the links to
        # all the other pages.
        if url == self.default_url:
            pagination_links = soup.find(
                'nav', {'class': 'pagination'}
            ).find_all('a')

            page_regex_results = self.PAGE_REGEX.search(
                pagination_links[-1].get('href')
            )

            pages_url_base = page_regex_results.group(1)
            pages = int(page_regex_results.group(2))

            return (
                discovered_episodes,
                pages_url_base,
                list(range(2, pages + 1))
            )

        return discovered_episodes

    def episode_worker(self, link):
        '''Extract the available sources from a link to an episode.'''

        episode_number_search = self.EPISODE_REGEX.search(link)

        if not episode_number_search:
            return

        episode_number = int(episode_number_search.group(1))
        print('[AnimeHaven] Processing episode {}'.format(episode_number))

        soup = self._as_soup(link)

        download_div = soup.find('div', {'class': 'download_feed_link'})

        if not download_div:
            return

        download_links = list(
            (x.find('span'), x.get('href'))
            for x in download_div.find_all('a')
        )

        _sources = []

        for quality_span, url in download_links:
            # For certain videos, the download link is available on the
            # website. We can directly fetch those links.
            if quality_span is not None:
                quality = int(
                    ''.join(x for x in quality_span.text if x.isdigit())
                )

                _sources.append((quality, url))

                continue

            # Else, we just try to use our unshortener
            __sources = unshorten(url)

            if not __sources:
                continue

            _sources += __sources

        print('[AnimeHaven] Done processing episode {}'.format(
            episode_number
        ))

        return (episode_number, _sources)
