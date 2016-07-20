import logging
import urllib
import time

import requests

from yajuu.media.sources import Source
from yajuu.config import config

logger = logging.getLogger(__name__)


class SourceList:

    def __init__(self):
        self._minimum_quality = config['media']['minimum_quality']
        self._maximum_quality = config['media']['maximum_quality']
        self.sources = []

    def __repr__(self):
        return str(self.sources)

    def __add__(self, other):
        source_list = SourceList()
        source_list.sources = self.sources + other.sources
        return source_list

    def __iter__(self):
        return iter(self.sources)

    def add_source(self, source):
        if source.quality < self._minimum_quality:
            return False

        if (
            self._maximum_quality > 0 and
            source.quality > self._maximum_quality
        ):
            return False

        self.sources.append(source)
        return True

    def add_sources(self, sources):
        if sources is None:
            return None

        results = []

        # If we have a source list
        if isinstance(sources, SourceList):
            iterator = sources.sources
        else:
            iterator = sources

        for source in iterator:
            results.append(self.add_source(source))

        return results

    def sorted(self):
        '''Sort the available sources by speed.'''

        # First, get the largest url netloc, so we can align the messages
        max_length = 0

        for source in self.sources:
            host_length = len(urllib.parse.urlparse(source.url).netloc)

            if host_length > max_length:
                max_length = host_length

        # Then, group the sources in a dict, cause we still want to preserve
        # quality over speed.
        by_quality = {}

        for source in self.sources:
            if source.quality not in by_quality:
                by_quality[source.quality] = []

            by_quality[source.quality].append(source)

        for quality in sorted(by_quality, reverse=True):
            sources = by_quality[quality]
            chunk_qualities = []

            if len(sources) <= 1:
                logger.debug(
                    'Only one source available for this quality, skipping '
                    'network speed sort.'
                )

                yield sources[0]
                continue

            print('Testing {} sources'.format(len(sources)))

            for source in sources:
                netloc = urllib.parse.urlparse(source.url).netloc
                offset = max_length - len(netloc)

                base = 'Testing source at {}.. {} '.format(
                    netloc, ' ' * offset
                )

                print(base, end='\r', flush=True)

                try:
                    response = requests.get(
                        source.url, stream=True, timeout=5,
                        headers={'Connection': 'close'}
                    )
                except (
                    requests.exceptions.ConnectTimeout,
                    requests.exceptions.ReadTimeout
                ):
                    print('{} timed out'.format(base))
                    continue

                size = 1e6  # Test over 1mb

                start = time.time()
                downloaded = 0

                for chunk in response.iter_content(chunk_size=1024):
                    downloaded += len(chunk)

                    print('{} {} bytes'.format(
                        base, downloaded
                    ), end='\r', flush=True)

                    if downloaded >= size:
                        break

                response_time = time.time() - start

                print('{0} {1} bytes downloaded in {2:.2f} seconds'.format(
                    base, downloaded, response_time
                ))

                chunk_qualities.append((response_time, source))

            # Now sort the chunk, fastest (smaller) first
            chunk_qualities = sorted(
                chunk_qualities, key=lambda x: x[0]
            )

            logger.debug((quality, chunk_qualities))

            # Remove the response time and re-add the quality
            for response_time, source in chunk_qualities:
                yield source
