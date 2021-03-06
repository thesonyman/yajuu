import logging
import difflib
from abc import ABCMeta, abstractmethod
import concurrent.futures

from yajuu.media.sources.source_list import SourceList

logger = logging.getLogger(__name__)


class Orchestrator(metaclass=ABCMeta):
    NOT_SEARCHED_EXCEPTION = Exception(
        'Can\'t extract before searching. Please call the search method.'
    )

    def __init__(self, media, extractors=None):
        self.media = media
        self.searched = False
        self.sources = SourceList()

        if extractors is None:
            self._extractors = self._create_extractors(
                self._get_default_extractors()
            )
        else:
            self._extractors = self._create_extractors(extractors)

    def _create_extractors(self, extractors):
        return dict((x(self.media), None) for x in extractors)

    def search(self, select_result=None):
        extractors = self._extractors.copy()

        for extractor, results in self._get_search_method(extractors):
            select_method = (
                self._select_result if not select_result else select_result
            )

            query = self.media.metadata['name'].lower()

            # Sort the results by similarity with the media name
            results = sorted(
                results,
                key=lambda x: difflib.SequenceMatcher(
                    a=query, b=x.title.lower()
                ).ratio(),
                reverse=True  # Better first
            )

            message = (
                'Please select the correct result for the media "{}", on '
                'website {}'
            ).format(
                self.media.metadata['name'],
                extractor._get_url()
            )

            result = select_result(extractor, query, message, results)

            if result:
                self._extractors[extractor] = result
            else:
                del self._extractors[extractor]

            print('')

        self.searched = True

    def _get_search_method(self, extractors):
        if logger.getEffectiveLevel() == logging.DEBUG:
            yield from self._sequential_search(extractors)
        else:
            yield from self._threaded_search(extractors)

    def _sequential_search(self, extractors):
        for extractor in extractors:
            try:
                results = extractor.search()
                yield (extractor, results)
            except Exception as e:
                logger.error(e)

    def _threaded_search(self, extractors):
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            futures = [
                executor.submit(self._threaded_search_worker, s)
                for s in extractors
            ]

            for future in concurrent.futures.as_completed(futures):
                data = future.result()

                if data:
                    yield data

    def _threaded_search_worker(self, extractor):
        try:
            results = extractor.search()
            return (extractor, results)
        except Exception as e:
            logger.error(e)

    def _select_result(self, extractor, query, message, results):
        # Get the correct result
        choice = None

        if len(results) <= 0:
            return False

        for index, row in enumerate(results):
            print('[{}] {}'.format(index, row.title))

        while choice is None:
            try:
                user_input = input(':: {} (0-{}) [0]: '.format(
                    message, len(results) - 1
                )).lower()
            except KeyboardInterrupt:
                choice = False
                continue

            if user_input == '':
                choice = results[0]
                continue
            elif user_input == '-1':
                choice = False
                continue

            try:
                index = int(user_input)
            except ValueError:
                continue

            if 0 <= index < len(results):
                choice = results[index]

        return choice

    def extract(self):
        if not self.searched:
            raise self.NOT_SEARCHED_EXCEPTION

        with concurrent.futures.ThreadPoolExecutor(6) as executor:
            executors_sources = executor.map(
                self._map_extractor_sources, self._extractors.items()
            )

            for sources in executors_sources:
                if sources:
                    self.sources += sources

        return self.sources

    def _map_extractor_sources(self, data):
        extractor, result = data
        extractor_name = type(extractor).__name__

        logger.info('[{}] Starting extractor'.format(extractor_name))

        try:
            extractor.extract(result)
            extractor_sources = extractor.sources
        except Exception as e:
            logger.exception('The extractor {} failed'.format(extractor_name))
            extractor_sources = None
        else:
            logger.info('[{}] Extractor done'.format(extractor_name))

        return extractor_sources

    def _get_default_extractors(self):
        return []
