from ..season_orchestrator import SeasonOrchestrator

from .anime_chiby import AnimeChibyExtractor
from .anime_haven import AnimeHavenExtractor
from .gogoanime_io import GogoAnimeIoExtractor
from .htvanime import HtvanimeExtractor


class AnimeOrchestrator(SeasonOrchestrator):
    def _get_query(self):
        return self.media.metadata['name']

    def _get_default_extractors(self):
        return [
            AnimeChibyExtractor, AnimeHavenExtractor, GogoAnimeIoExtractor,
            HtvanimeExtractor
        ]
