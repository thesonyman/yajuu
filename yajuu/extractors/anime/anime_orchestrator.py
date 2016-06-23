from ..season_orchestrator import SeasonOrchestrator


class AnimeOrchestrator(SeasonOrchestrator):
    def _get_query(self):
        return self.media.metadata['name']
