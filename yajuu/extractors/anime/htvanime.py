import concurrent.futures
import urllib.parse
import json

import requests

from .anime_extractor import AnimeExtractor


class HtvanimeExtractor(AnimeExtractor):
    def search(self):
        # Fetch all the pages
        page = 0
        pages_count = 1
        results = []

        while page < pages_count:
            response = requests.post(
                'https://sjzdlecc2z-dsn.algolia.net/1/indexes/Anime/query?x-'
                'algolia-agent=Algolia%20for%20vanilla%20JavaScript%203.14.6&x'
                '-algolia-application-id=SJZDLECC2Z&x-algolia-api-key='
                'caa4878bcf6f8aea380e73b5840ff22b',

                json={
                    'params': urllib.parse.urlencode({
                        'query': self.media.metadata['name'],
                        'hitsPerPage': 10,
                        'page': page
                    })
                }
            ).json()

            page += 1

            pages_count = int(response['nbPages'])

            for hit in response['hits']:
                results.append((hit['title'], hit['slug']))

        return results

    def extract(self, season, result):
        base_url = (
            'http://api.htvanime.com/api/v1/anime_episodes?anime_slug={}'
        )

        response = requests.get(base_url.format(result[1])).json()

        sources = {}

        with concurrent.futures.ThreadPoolExecutor(16) as executor:
            for episode_number, _sources in filter(
                lambda x: x,  # Filter out the None values
                executor.map(self.map_sources, response['data'])
            ):
                if episode_number not in sources:
                    sources[episode_number] = []

                sources[episode_number] += _sources

        return sources

    def map_sources(self, episode):
        retries = 0
        success = False
        episode_response = None

        while retries < 10 and not success:
            url = (
                'http://api.htvanime.com/api/v1/anime_episode_videos/?'
                'anime_episode_slug={}'
            ).format(episode['slug'])

            try:
                # We have a lot of 500 errors there..
                episode_response = requests.get(url, timeout=3).json()

                if episode_response is not None:
                    break
                else:
                    retries += 1
            except (
                json.decoder.JSONDecodeError,
                requests.exceptions.ReadTimeout
            ):
                retries += 1
                print('-> retry::({})'.format(retries))

        # TODO: special episodes
        if not episode['episode_number']:
            return None

        episode_number = int(episode['episode_number'])
        print('[Htvanime] Processing episode {}'.format(episode_number))

        _sources = []

        for source in episode_response:
            _sources.append((
                int(''.join(x for x in source['quality'] if x.isdigit())),
                source['url']
            ))

        return (episode_number, _sources)
