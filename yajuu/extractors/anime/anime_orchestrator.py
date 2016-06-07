from ..season_orchestrator import SeasonOrchestrator


class AnimeOrchestrator(SeasonOrchestrator):
    def __init__(self, extractors, media, season):
        super().__init__(extractors, media, season)

        # After the supper call, else the value is overwritten.
        self.query = media.metadata['name']
