import re
import concurrent.futures

import unshortenit

from .anime_extractor import AnimeExtractor
from ..unshorten import unshorten


class AnimeChibyExtractor(AnimeExtractor):
    def search(self):
        soup = self._as_soup('http://www.animechiby.com?{params}', params={
            's': self.media.metadata['name']
        })

        # Those are only 'top-level' links. The site organize contents in such
        # a way that the users can post an item, and in this item, multiple
        # medias can be found. We wanna fetch all those links.
        links = soup.select('.post h2 > a')

        # Well, the website uses window.open instead of href, for no apparent
        # reason.
        onclick_regex = re.compile(
            r'window\.open\([\'|\"](.+)[\'|\"]\);return false;'
        )

        results = []

        for link in links:
            link_soup = self._as_soup(link.get('href'))

            # We get all the available sub-links for each link
            for section in link_soup.select('.su-spoiler'):
                # The section title
                sub_title = section.select('.su-spoiler-title')[0].text

                # We get all the sources.
                available_sources = list((
                    x.get('value'),
                    re.search(onclick_regex, x.get('onclick')).group(1)
                ) for x in section.find_all('input'))

                # We determine the section title, that is the top-level title
                # concatenated with the section title.
                block_title = '-> {} ({})'.format(link.text, sub_title)

                results.append((block_title, available_sources))

        return results

    def extract(self, season, result):
        sources = {}

        with concurrent.futures.ThreadPoolExecutor(16) as executor:
            # The website offer two kinds of links. The first one offer
            # directly the episodes as the links. The second redirects to a
            # page which list the links.

            # There should not be mixed cases, but we never now. We will
            # process each case every time.
            first_case_links = []
            second_case_links = []

            for input_title, link in result[1]:
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
                    soup = self._as_soup(unshortenit.unshorten(link)[0])
                    second_case_links += soup.select('td a[target="_BLANK"]')

            first_case_sources = list(executor.map(
                self.map_first_case, first_case_links
            ))

            second_case_sources = list(executor.map(
                self.map_second_case, second_case_links
            ))

            for episode_number, episode_sources in (
                x for x in first_case_sources + second_case_sources
                if x is not None
            ):
                if not episode_sources:
                    continue

                if episode_number not in sources:
                    sources[episode_number] = []

                sources[episode_number] += episode_sources

        return sources

    def map_first_case(self, data):
        '''For the first case, get the real link and extract the episode
        number.'''

        input_title, link = data

        episode_number = int(''.join(
            c for c in input_title if c.isdigit()
        ))

        print('[AnimeChiby] Processing episode {}'.format(
            episode_number
        ))

        results = (episode_number, unshorten(link))

        print('[AnimeChiby] Done Processing episode {}'.format(
            episode_number
        ))

        return results

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

        print('[Animechiby] Processing episode {}'.format(
            episode_number
        ))

        # The links are shortened there too..
        episode_link = unshortenit.unshorten(
            episode_link.get('href')
        )[0]

        _sources = unshorten(episode_link)

        print('[AnimeChiby] Finished processing episode {}'.format(
            episode_number
        ))

        if not _sources:
            return None

        return (episode_number, _sources)
