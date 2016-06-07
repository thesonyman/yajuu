from .orchestrator import Orchestrator


class SeasonOrchestrator(Orchestrator):
    def __init__(self, extractors, media, season):
        self.season = season
        self.seasons = {}
        super().__init__(extractors, media)

    def _create_extractors(self, extractors):
        self.extractors = (e(
            self.media, self.season
        ) for e in extractors)
