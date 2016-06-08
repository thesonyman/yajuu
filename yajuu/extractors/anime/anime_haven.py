import re

from .anime_extractor import AnimeExtractor
from ..unshorten import unshorten


class AnimeHavenExtractor(AnimeExtractor):
    def search(self):
        soup = self._as_soup(
            'http://animehaven.org/wp-admin/admin-ajax.php',
            data={
                'action': 'search_ajax',
                'keyword': self.media.metadata['name']
            }
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
        page = 1
        pages = 1
        pages_url_base = None
        url = result[1]

        page_regex = re.compile(r'(http://.+/page/)([0-9]+)')
        episode_regex = re.compile(r'http://.+-episode-([0-9]+)')

        discovered_episodes = []

        while page <= pages:
            soup = self._as_soup(url)

            # We first try to determinate how much pages there is to process
            if page == 1:
                pagination_links = soup.find(
                    'nav', {'class': 'pagination'}
                ).find_all('a')

                page_regex_results = re.search(
                    page_regex, pagination_links[-1].get('href')
                )

                pages_url_base = page_regex_results.group(1)
                pages = int(page_regex_results.group(2))

            # The episodes are listed on each page as posts.
            episodes = soup.find_all('article', {'class': 'post'})
            discovered_episodes += list(
                x.find('h2').find('a').get('href') for x in episodes
            )

            page += 1
            url = pages_url_base + str(page)

        sources = {}

        # Now that we have all the internal links, we can fetch the real ones
        for link in discovered_episodes:
            episode_number_search = re.search(episode_regex, link)

            if not episode_number_search:
                continue

            episode_number = int(episode_number_search.group(1))
            print('[AnimeHaven] Processing episode {}'.format(episode_number))

            soup = self._as_soup(link)

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
                # For certain videos, the download link is available on the
                # website. We can directly fetch those links.
                if quality_span is not None:
                    quality = int(
                        ''.join(x for x in quality_span.text if x.isdigit())
                    )

                    sources[episode_number].append((quality, url))

                    continue

                # Else, we just try to use our unshortener
                sources = unshorten(url)

                if not sources:
                    continue

                sources[episode_number] += sources

        return sources
