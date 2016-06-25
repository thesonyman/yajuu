import difflib
from abc import ABCMeta, abstractmethod
import concurrent.futures

from yajuu._cli.utils import select


class Orchestrator(metaclass=ABCMeta):
    NOT_SEARCHED_EXCEPTION = Exception(
        'Can\'t extract before searching. Please call the search method.'
    )

    def __init__(self, media, extractors=None):
        self.media = media
        self.searched = False

        if extractors == None:
            self._extractors = self._create_extractors(
                self._get_default_extractors()
            )
        else:
            self._extractors = self._create_extractors(extractors)

    def _create_extractors(self, extractors):
        return dict((x(self.media), None) for x in extractors)

    def search(self, select_result=None):
        extractors = self._extractors.copy()

        for extractor in extractors:
            select_method = (
                self._select_result if not select_result else select_result
            )

            query = self.media.metadata['name'].lower()

            # Sort the results by similarity with the media name
            results = sorted(
                extractor.search(),
                key=lambda x: difflib.SequenceMatcher(
                    a=query, b=x[0].lower()
                ).ratio(),
                reverse=True  # Better first
            )

            result = select_result(extractor, query, (
                'Please select the correct result for the media "{}"'.format(
                    self.media.metadata['name']
                )
            ), results)

            if result:
                self._extractors[extractor] = result
            else:
                del self._extractors[extractor]

            print('')

        self.searched = True

    def _select_result(self, extractor, query, message, results):
        # Get the correct result
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

    def _get_default_extractors(self):
        return []
