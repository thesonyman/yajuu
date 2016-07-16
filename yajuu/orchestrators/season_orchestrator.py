import concurrent.futures
import difflib
import logging

from . import Orchestrator
from yajuu.media import SourceList

logger = logging.getLogger(__name__)


class SeasonOrchestrator(Orchestrator):

    def __init__(self, media, seasons, extractors=None):
        self._seasons = seasons
        super().__init__(media, extractors=extractors)
        self.sources = {}

    def _create_extractors(self, extractors):
        _extractors = {}

        for season in self._seasons:
            _extractors[season] = dict(
                (x(self.media, season), None) for x in extractors.copy()
            )

        return _extractors

    def search(self, select_result=None):
        for season in self._seasons:
            extractors = self._extractors[season].copy()

            for extractor, results in self._get_search_method(extractors):
                select_method = (
                    self._select_result if not select_result else select_result
                )

                query = self.media.metadata['name'].lower()

                logger.debug('Starting extractor {}'.format(
                    type(extractor).__name__
                ))

                # Sort the results by similarity with the media name
                results = sorted(
                    results,
                    key=lambda x: difflib.SequenceMatcher(
                        a=query, b=x.title.lower()
                    ).ratio(),
                    reverse=True  # Better first
                )

                message = (
                    'Please select the correct result for the media "{}"'
                    ', season {}, website "{}"'
                ).format(
                    self.media.metadata['name'], season,
                    extractor._get_url()
                )

                result = select_method(extractor, query, message, results)

                if result:
                    self._extractors[season][extractor] = result
                else:
                    del self._extractors[season][extractor]

        self.searched = True

    def extract(self):
        if not self.searched:
            raise self.NOT_SEARCHED_EXCEPTION

        for season in self._seasons:
            self.sources[season] = {}

            with concurrent.futures.ThreadPoolExecutor(6) as executor:
                for sources in executor.map(
                    self._map_extractor_sources,
                    ((extractor, season, result)
                     for extractor, result in self._extractors[season].items())
                ):
                    if not sources:
                        continue

                    for identifier, source_list in sources.items():
                        if identifier not in self.sources[season]:
                            self.sources[season][identifier] = SourceList()

                        self.sources[season][identifier] += source_list

        return self.sources

    def _map_extractor_sources(self, data):
        extractor, season, result = data
        extractor_name = type(extractor).__name__

        logger.info('INFO: [{}] Starting extractor'.format(extractor_name))

        try:
            extractor.extract(season, result)
            extractor_sources = extractor.sources
        except Exception as e:
            logger.exception('The extractor {} failed'.format(extractor_name))
            extractor_sources = None
        else:
            logger.info('[{}] Extractor done'.format(extractor_name))

        return extractor_sources
