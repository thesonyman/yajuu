import difflib
from abc import ABC, abstractmethod

from yajuu.cli.utils import select


class Orchestrator(ABC):
    def __init__(self, extractors, media):
        self.media = media
        self._create_extractors(extractors)

    def _get_query(self):
        pass

    @abstractmethod
    def _create_extractors(self, extractors):
        pass

    @abstractmethod
    def _get_select_message(self, extractor):
        pass

    def search(self):
        extractors_with_identifiers = {}
        query = self._get_query()

        for extractor in self.extractors:
            results = extractor.search()

            # Sort the results by similarity with the media title
            results = sorted(results, key=lambda x: difflib.SequenceMatcher(
                a=query.lower(), b=x[0].lower()
            ).ratio(), reverse=True)  # Better first

            message = self._get_select_message(extractor)

            result = select(message, results)

            if result:
                extractors_with_identifiers[extractor] = result

        self.extractors = extractors_with_identifiers

    def extract(self):
        if type(self.extractors) == list:
            raise Exception(
                "Can't extract before searching. Please call search."
            )

        sources = {}

        for extractor, result in self.extractors.items():
            extractor_sources = extractor.extract(result)
            sources.update(extractor_sources)

        return sources
