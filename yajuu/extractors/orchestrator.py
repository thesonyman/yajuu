import difflib
from abc import ABC, abstractmethod
import concurrent.futures

from yajuu.cli.utils import select


class Orchestrator(ABC):
    NOT_SEARCHED_EXCEPTION = Exception(
        'Can\'t extract before searching. Please call the search method.'
    )

    def __init__(self, extractors, media):
        self.media = media
        self.searched = False
        self._extractors = self._create_extractors(extractors)

    def _create_extractors(self, extractors):
        return dict((x(self.media), None) for x in extractors)

    def search(self):
        extractors = self._extractors.copy()

        for extractor in extractors:
            result = self._select_result(extractor, (
                'Please select the correct result for the media "{}"'.format(
                    self.media.metadata['name']
                )
            ))

            if result:
                self._extractors[extractor] = result
            else:
                del self._extractors[extractor]

            print('')

        self.searched = True

    def _select_result(self, extractor, message):
        query = self.media.metadata['name'].lower()

        # Sort the results by similarity with the media name
        results = sorted(
            extractor.search(),
            key=lambda x: difflib.SequenceMatcher(
                a=query, b=x[0].lower()
            ).ratio(),
            reverse=True  # Better first
        )

        # And get the correct result
        return select(message, results)

    def extract(self):
        if not self.searched:
            raise self.NOT_SEARCHED_EXCEPTION

        sources = {}

        with concurrent.futures.ThreadPoolExecutor(6) as executor:
            executors_sources = executor.map(
                self._map_extractor_sources, self._extractors.items()
            )

            for ep_number, episode_sources in executors_sources.items():
                if ep_number not in sources:
                    sources[ep_number] = []

                sources[ep_number] += episode_sources

        return sources

    def _map_extractor_sources(self, data):
        extractor, result = data
        extractor_name = type(extractor).__name__

        print('[{}] Starting extractor'.format(extractor_name))
        extractor_sources = extractor.extract(result)
        print('[{}] Extractor done'.format(extractor_name))

        return extractor_sources
