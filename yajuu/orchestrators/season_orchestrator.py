import concurrent.futures
import difflib
import logging

from . import Orchestrator

logger = logging.getLogger(__name__)


class SeasonOrchestrator(Orchestrator):
    def __init__(self, media, seasons, extractors=None):
        self._seasons = seasons
        super().__init__(media, extractors=extractors)

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

            for extractor in extractors:
                select_method = (
                    self._select_result if not select_result else select_result
                )

                query = self.media.metadata['name'].lower()

                logger.debug('Starting extractor {}'.format(
                    type(extractor).__name__
                ))

                # Sort the results by similarity with the media name
                results = sorted(
                    extractor.search(),
                    key=lambda x: difflib.SequenceMatcher(
                        a=query, b=x[0].lower()
                    ).ratio(),
                    reverse=True  # Better first
                )

                result = select_method(extractor, query, (
                    'Please select the correct result for the media "{}", '
                    'season {}, website "{}"'.format(
                        self.media.metadata['name'], season,
                        extractor._get_url()
                    )
                ), results)

                if result:
                    self._extractors[season][extractor] = result
                else:
                    del self._extractors[season][extractor]

        self.searched = True

    def extract(self):
        if not self.searched:
            raise self.NOT_SEARCHED_EXCEPTION

        sources = {}

        for season in self._seasons:
            sources[season] = {}

            with concurrent.futures.ThreadPoolExecutor(6) as executor:
                executors_sources = executor.map(self._map_extractor_sources, (
                    (x[0], season, x[1])
                    for x in self._extractors[season].items()
                ))

                for season, executor_sources in executors_sources:
                    if not executor_sources:
                        continue

                    for ep_number, episode_sources in executor_sources.items():
                        if ep_number not in sources[season]:
                            sources[season][ep_number] = []

                        sources[season][ep_number] += episode_sources

        return sources

    def _map_extractor_sources(self, data):
        extractor, season, result = data
        extractor_name = type(extractor).__name__

        logger.info('INFO: [{}] Starting extractor'.format(extractor_name))

        try:
            extractor_sources = extractor.extract(season, result)
        except Exception as e:
            logger.exception('The extractor {} failed'.format(extractor_name))
            extractor_sources = None
        else:
            logger.info('[{}] Extractor done'.format(extractor_name))

        return (season, extractor_sources)
