import difflib

from yajuu.cli.utils import select
from .orchestrator import Orchestrator


class SeasonOrchestrator(Orchestrator):
    def __init__(self, extractors, media, season):
        self.season = season
        super().__init__(extractors, media)

    def _create_extractors(self, extractors):
        self.extractors = list(e(
            self.media, self.season
        ) for e in extractors)

    def _get_select_message(self, extractor, season):
        return (
            'For the extractor "{}", season {}, please select the correct '
            'result'
        ).format(type(extractor).__name__, season)

    def search(self):
        extractors_with_identifiers = {}
        query = self._get_query()

        for season in self.season:
            extractors_with_identifiers[season] = {}

            for extractor in self.extractors:
                results = extractor.search()

                # Sort the results by similarity with the media title
                results = sorted(
                    results,
                    key=lambda x: difflib.SequenceMatcher(
                        a=query.lower(), b=x[0].lower()
                    ).ratio(),
                    reverse=True
                )

                message = self._get_select_message(extractor, season)

                result = select(message, results)

                if result:
                    extractors_with_identifiers[season][extractor] = result

        self.extractors = extractors_with_identifiers

    def extract(self):
        if type(self.extractors) == list:
            raise Exception(
                "Can't extract before searching. Please call search."
            )

        sources = {}

        for season, extractors in self.extractors.items():
            sources[season] = {}

            for extractor, result in extractors.items():
                extractor_sources = extractor.extract(season, result)

                for episode_number, episode_sources in extractor_sources.items():
                    if episode_number not in sources[season]:
                        sources[season][episode_number] = []

                    for source in episode_sources:
                        sources[season][episode_number].append(source)

        return sources
