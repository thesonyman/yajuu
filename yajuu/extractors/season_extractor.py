from yajuu.extractors.extractor import Extractor
from yajuu.media.sources.source_list import SourceList


class SeasonExtractor(Extractor):

    def __init__(self, media, season, range_):
        super().__init__(media)
        self.seasons = {}
        self.season = season
        self.start, self.end = range_

        # Overwrite
        self.sources = {}

    def _should_process(self, episode_identifier):
        try:
            episode_number = int(episode_identifier)
        except ValueError:
            return False

        return self.start <= episode_number <= self.end


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
