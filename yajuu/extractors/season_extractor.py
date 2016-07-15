from . import Extractor
from yajuu.media import SourceList


class SeasonExtractor(Extractor):

    def __init__(self, media, season):
        super().__init__(media)
        self.seasons = {}
        self.season = season

        # Overwrite
        self.sources = {}

    def _add_source(self, identifier, source):
        if identifier not in self.sources:
            self.sources[identifier] = SourceList()

        self.sources[identifier].add_source(source)

        return True

    def _add_sources(self, identifier, sources):
        returned = []

        if sources is None:
            return

        for source in sources:
            returned.append(self._add_source(identifier, source))

        return returned
