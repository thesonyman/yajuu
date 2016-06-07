import difflib
from abc import ABC, abstractmethod


class Orchestrator(ABC):
    def __init__(self, extractors, media):
        self.media = media
        self.query = None

        self._create_extractors(extractors)

    @abstractmethod
    def _create_extractors(self, extractors):
        pass

    def search(self):
        extractors_with_identifiers = {}

        for extractor in self.extractors:
            results = extractor.search()

            # Sort the results by similarity with the media title
            results = sorted(results, key=lambda x: difflib.SequenceMatcher(
                a=self.query.lower(), b=x[0].lower()
            ).ratio(), reverse=True)  # Better first

            for i in results:
                print(i)

            extractors_with_identifiers[extractor] = results

        self.extractors = extractors_with_identifiers

    def extract(self):
        if type(self.extractors) == list:
            raise Exception(
                "Can't extract before searching. Please call search."
            )

        print(self.extractors)
